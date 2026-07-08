import time
import anyio
from core.search.query_embedding import embed_query
from core.search.candidate_retrieval import retrieve_candidates_range
from core.search.load_docs import load_grant_texts
from core.search.combine import combine_and_sort
from core.search.postprocess import dedupe_by_core_project

async def hybrid_search_range(
    query: str,
    cur,rerank_fn,
    similarity_threshold: float = 0.25,
    search_mode: str = "hybrid"
    
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

    Returns
    -------
    dict
        A dictionary containing:

        - ``query``: the original query string.
        - ``model_version``: a string identifier for the search model version.
        - ``projects``: a list of deduplicated project records returned by the search.
        - ``records``: a list of all ranked records prior to deduplication.
    """

    t0 = time.perf_counter()
   
    query_vec = embed_query(query)
    query_vec_list = query_vec.tolist()

    print(f"Query embedded in {time.perf_counter() - t0:.4f}s")

    # 2) Retrieve candidates via pgvector
    t1 = time.perf_counter()
    candidates = await anyio.to_thread.run_sync(
        retrieve_candidates_range, 
        cur, 
        query_vec_list, 
        similarity_threshold,
        query_text=query,
        search_mode=search_mode
    )
    print(f"Candidates retrieved in {time.perf_counter() - t1:.4f}s")

    if not candidates:
        return {
            "query": query,
            "model_version": "v1",
            "projects": [],
            "records": []
        }

    print(f"Retrieved {len(candidates)} candidates.")

    t2 = time.perf_counter()
    vector_sim_map = {gid: sim for gid, sim in candidates}
    grant_ids = list(vector_sim_map.keys())

    print("Loading document texts...")

    # 3) Rerank with cross-encoder (Passing ONLY IDs over the internet!) 🚀
    print("Sending IDs to Modal for remote Cross-Encoder scoring...")
    t2 = time.perf_counter()
    
    # Use updated async/batch setup
    scores = await rerank_fn.remote.aio(query, grant_ids)
    
    print(f"Candidates reranked on remote GPU in {time.perf_counter() - t2:.4f}s")

    # ⚠️ SAFETY ALIGNMENT: Match grant_ids exactly to what Modal actually scored
    if len(grant_ids) != len(scores):
        print(f"⚠️ Mismatch: {len(grant_ids)} grant_ids sent, but {len(scores)} scores returned")
        return {
            "query": query,
            "model_version": "v1",
            "projects": [],
            "records": []
        }

    # 4) Hydrate Document Metadata locally *ONLY FOR SUCCESSFUL MATCHES*
    print("Loading document metadata/titles for scored records...")
    t3 = time.perf_counter()
    
    # Pull data out of Postgres locally to render your frontend cards
    docs = await anyio.to_thread.run_sync(load_grant_texts, cur, grant_ids)
        
    print(f"Document metadata loaded in {time.perf_counter() - t3:.4f}s")
    if not docs:
        return {
            "query": query,
            "model_version": "v1",
            "projects": [],
            "records": []
        }

    # Inject vector distance profiles into our database docs array
    for d in docs:
        d["vector_similarity"] = vector_sim_map.get(d["grant_id"], 0.0)
            
    # 5) Combine scores + Sort + Deduplicate
    t4 = time.perf_counter()
    print("Combining, sorting, and deduplicating final results...")
    
    ranked = combine_and_sort(docs, scores)
    deduped = dedupe_by_core_project(ranked)

    print(f"Results combined and deduplicated in {time.perf_counter() - t4:.4f}s")
    print(f"Returning {len(deduped)} top matching projects.")

    return {
        "query": query,
        "model_version": "v1",
        "projects": deduped,
        "records": ranked
    }
