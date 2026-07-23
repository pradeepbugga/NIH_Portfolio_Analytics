import time
import anyio

import logging

from core.search.query_embedding import embed_query
from core.search.candidate_retrieval import retrieve_candidates_range
from core.search.load_docs import load_grant_texts
from core.search.combine import combine_and_sort
from core.search.postprocess import dedupe_by_core_project
from core.utils.query_expansion import expand_query_for_fts


logger = logging.getLogger(__name__)

async def hybrid_search_range(
    query: str,
    cur,
    rerank_fn,
    similarity_threshold: float = 0.20,
    search_mode: str = "hybrid",
    synonym_registry: dict = None,
    fiscal_years=None,
    rerank_score_threshold: float = -2.0,
):
    """
    Perform semantic search over NIH grant documents within a similarity range.

    This function embeds the input query, retrieves candidate grants based on vector
    similarity, loads the corresponding grant texts, reranks the candidates using a
    cross-encoder, combines and sorts the results, and deduplicates them by core
    project before returning the final results.

    Parameters
    ----------
    query : str
        The natural language search query provided by the user.
    cur
        A database cursor used to execute queries against the grants database.
    similarity_threshold : float
        Minimum vector similarity score required for a grant to be considered as
        a candidate during retrieval. Defaults to 0.25.
    search_mode : str
        The search mode to use for candidate retrieval. Can be either "semantic" for purely semantic search or
        "hybrid" for a combination of semantic and keyword search. Defaults to "hybrid".
    synonym_registry : dict
        A dictionary mapping query terms to their synonyms for query expansion. If None, no synonyms will be used. Defaults to None.
    fiscal_years : list
        A list of fiscal years to filter the grants by. If None, no fiscal year filtering will be applied. Defaults to None.
    rerank_score_threshold : float
        Minimum reranker score required for a grant to be included in the final results. Grants with reranker scores below this threshold will be excluded. Defaults to -2.0.

    Returns
    -------
    dict
        A dictionary containing:

        - ``query``: the original query string.
        - ``model_version``: a string identifier for the search model version.
        - ``projects``: a list of deduplicated project records returned by the search.
        - ``records``: a list of all ranked records prior to deduplication.
        - ``candidates``: a list of candidate grants retrieved based on vector similarity prior to reranking. Each candidate is represented as a tuple of (grant_id, similarity_score).
    """

    t0 = time.perf_counter()

    query_vec = embed_query(query)
    query_vec_list = query_vec.tolist()

    logger.info("Query embedded in %.4fs", time.perf_counter() - t0)

    # 1b) Extract synonyms cleanly as an isolated list before running thread 🚀
    base_query, query_synonyms = expand_query_for_fts(query, synonym_registry or {})

    # 2) Retrieve candidates via pgvector
    t1 = time.perf_counter()
    candidates = await anyio.to_thread.run_sync(
        retrieve_candidates_range,
        cur,
        query_vec_list,
        similarity_threshold,
        base_query,  # Pass clean string text parameter
        search_mode,
        query_synonyms,  # 👈 Pass clean Python list parameter ([])
        fiscal_years,  # Pass fiscal_years parameter (None or list)
        500000,  # max_results explicitly filled positionally
    )

    logger.info("Candidates retrieved in %.4fs", time.perf_counter() - t1)

    if not candidates:
        return {
            "query": query,
            "model_version": "v1",
            "projects": [],
            "records": [],
            "candidates": [],  # Include empty candidates for debugging
        }

    logger.info("Retrieved %d candidates for query '%s'", len(candidates), query)

    t2 = time.perf_counter()
    vector_sim_map = {gid: sim for gid, sim in candidates}
    grant_ids = list(vector_sim_map.keys())


    # 3) Rerank with cross-encoder (Passing ONLY IDs over the internet!) 🚀
    t2 = time.perf_counter()

    # Use updated async/batch setup
    scores = await rerank_fn.remote.aio(query, grant_ids)

    logger.info(
        "Candidates reranked on remote GPU in %.4fs", time.perf_counter() - t2
    )

    # ⚠️ ALIGNMENT: Match grant_ids exactly to what Modal actually scored
    if len(grant_ids) != len(scores):
        logger.warning(
            "Mismatch: %d grant_ids sent, but %d scores returned",
            len(grant_ids),
            len(scores),
        )
        return {"query": query, "model_version": "v1", "projects": [], "records": []}

    # 4) Hydrate Document Metadata locally *ONLY FOR SUCCESSFUL MATCHES*
    t3 = time.perf_counter()

    # Pull data out of Postgres locally to render your frontend cards
    docs = await anyio.to_thread.run_sync(load_grant_texts, cur, grant_ids)

    logger.info(
        "Document metadata loaded in %.4fs for %d grants",
        time.perf_counter() - t3,
        len(docs),
    )

    if not docs:
        return {"query": query, "model_version": "v1", "projects": [], "records": []}

    # Inject vector distance profiles into our database docs array
    for d in docs:
        d["vector_similarity"] = vector_sim_map.get(d["grant_id"], 0.0)

    # 5) Combine scores + Sort + Deduplicate
    t4 = time.perf_counter()

    ranked = combine_and_sort(docs, scores, rerank_score_threshold)
    deduped = dedupe_by_core_project(ranked)

    logger.info(
        "Results combined, sorted, and deduplicated in %.4fs",
        time.perf_counter() - t4,
    )
    logger.info("Returning %d top matching projects for query '%s'", len(deduped), query)

    return {
        "query": query,
        "model_version": "v1",
        "projects": deduped,
        "records": ranked,
        "candidates": candidates,  # Include raw candidates for debugging
    }
