# search_service_prod.py
# this script provides a semantic search service for NIH grant documents
# we use similarity search here for high recall

from core.search.query_embedding import embed_query
from core.search.candidate_retrieval import retrieve_candidates_range
from core.search.load_docs import load_grant_texts
from core.search.reranker import rerank_batch
from core.search.combine import combine_and_sort
from core.search.postprocess import dedupe_by_core_project
import time

def semantic_search_range(
    query: str,
    cur,
    similarity_threshold: float = 0.25,

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

    Returns
    -------
    dict
        A dictionary containing:

        - ``query``: the original query string.
        - ``model_version``: a string identifier for the search model version.
        - ``projects``: a list of deduplicated project records returned by the search.
        - ``records``: a list of all ranked records prior to deduplication.
    """

   
    query_vec = embed_query(query)
    query_vec_list = query_vec.tolist()

    # 2) Retrieve candidates via pgvector
    candidates = retrieve_candidates_range(cur, query_vec_list=query_vec_list, similarity_threshold=similarity_threshold)
    
    if not candidates:
        return {
            "query": query,
            "model_version": "v1",
            "projects": [],
            "records": []
        }


    print(f"Retrieved {len(candidates)} candidates.")

    vector_sim_map = {gid: sim for gid, sim in candidates}
    grant_ids = list(vector_sim_map.keys())

    print("Loading document texts...")

    # 3) Load document texts + metadata
    docs = load_grant_texts(cur, grant_ids)
    if not docs:
        return {
            "query": query,
            "model_version": "v1",
            "projects": [],
            "records": []
        }
    
    print(f"Loaded {len(docs)} documents.")

    for d in docs:
        d["vector_similarity"] = vector_sim_map.get(d["grant_id"], 0.0)
            
    print("Reranking candidates...")

    # 4) Rerank with cross-encoder
    doc_texts = [d["text"] for d in docs]
    scores = rerank_batch(query, doc_texts)

    print("Combining and sorting results...")

    # 5) Combine + sort
    ranked = combine_and_sort(docs, scores)
  
    print("Deduplicating by core project...")
    # 6) Deduplicate by core project
    deduped = dedupe_by_core_project(ranked)

    #return deduped list
    print(f"Returning {len(deduped)} results")


    #output a JSON to allow downstream processing and visualization
    output = {
        "query": query,
        "model_version": "v1",
        "projects": deduped,
        "records": ranked
    }

    return output