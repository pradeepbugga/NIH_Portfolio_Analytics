# this script retrieves candidate NIH grants based on embedding similarity
# you can use either top-k or range-based retrieval (latter preferred for our high recall application)

from core.utils.query_expansion import expand_query_for_fts

def retrieve_candidates_topk(cur, query_vec, top_k=200):
    
    # Convert numpy array → Python list
    query_vec = query_vec.tolist()
    
    cur.execute(
        """
        SELECT
            ge.grant_id,
            1 - (ge.embedding <=> %s::vector) AS similarity
        FROM GrantEmbeddings ge
        WHERE ge.is_valid = TRUE
        ORDER BY ge.embedding <=> %s::vector
        LIMIT %s
        """,
        (query_vec, query_vec, top_k)
    )
    return cur.fetchall()

#we set max results at 500K to ensure we get a sufficient number of candidates for high recall
def retrieve_candidates_range(
    cur, 
    query_vec_list: list, 
    similarity_threshold: float, 
    query_text: str = None, 
    search_mode: str = "semantic", 
    synonym_registry: dict = None,
    max_results: int = 500000
):
    """
    Retrieve candidate grants using either purely semantic or hybrid search.
    """
    # --- 1. SEMANTIC TRACK ---
    cur.execute(
        """
        SELECT grant_id, 1 - d AS similarity
        FROM (
            SELECT grant_id, (embedding <=> %s::vector) AS d
            FROM GrantEmbeddings
            WHERE is_valid = TRUE
        ) ge
        WHERE d <= %s
        ORDER BY d
        LIMIT %s
        """,
        (query_vec_list, 1 - similarity_threshold, max_results)
    )
    semantic_results = cur.fetchall()
    
    # Return early if purely semantic or if no text was provided
    if search_mode == "semantic" or not query_text:
        return semantic_results

    # --- 2. KEYWORD TRACK (HYBRID ONLY) ---
    synonyms = get_query_synonyms(query_text, synonym_registry or {}) if synonym_registry else []

    # Construct the query using standard SQL array operations for synonyms.
    # This prevents syntax errors and ensures the index is fully utilized.
    cur.execute(
        """
        SELECT rg.grant_id
        FROM ResearchGrants rg
        JOIN GrantEmbeddings ge ON rg.grant_id = ge.grant_id
        WHERE ge.is_valid = TRUE 
          AND (
            -- Handle the main multi-word phrase safely
            to_tsvector('simple', COALESCE(rg.project_title, '') || ' ' || COALESCE(rg.abstract, '')) 
                @@ websearch_to_tsquery('simple', %s)
            
            -- Seamlessly fall back to looking up any matching short acronym tokens
            OR (
                cardinality(%s::text[]) > 0 
                AND to_tsvector('simple', COALESCE(rg.project_title, '') || ' ' || COALESCE(rg.abstract, '')) 
                    @@ to_tsquery('simple', array_to_string(%s::text[], ' | '))
            )
          )
        LIMIT %s;
        """,
        (query_text, synonyms, synonyms, max_results)
    )
    keyword_results = cur.fetchall()

    # --- 3. MERGE & DEDUPLICATE ---
    candidate_map = {grant_id: sim for grant_id, sim in semantic_results}
    
    for (grant_id,) in keyword_results:
        if grant_id not in candidate_map:
            # Baseline similarity for keyword-only matches. 
            # The Modal Cross-Encoder will compute the final true rank score anyway!
            candidate_map[grant_id] = 0.0  

    return list(candidate_map.items())

def retrieve_candidates_range_portfolio(
    cur,
    query_vec_list,
    similarity_threshold,
    max_results=500000,
    allowed_grant_ids=None
):

    # -----------------------------------------
    # ONTOLOGY-CONSTRAINED VECTOR RETRIEVAL
    # -----------------------------------------

    if allowed_grant_ids:

        cur.execute(
            """
            SELECT grant_id, 1 - d AS similarity
            FROM (
                SELECT
                    grant_id,
                    (embedding <=> %s::vector) AS d
                FROM GrantEmbeddings
                WHERE
                    is_valid = TRUE
                    AND grant_id = ANY(%s)
            ) ge
            WHERE d <= %s
            ORDER BY d
            LIMIT %s
            """,
            (
                query_vec_list,
                allowed_grant_ids,
                1 - similarity_threshold,
                max_results,
            )
        )

    # -----------------------------------------
    # GLOBAL VECTOR RETRIEVAL
    # -----------------------------------------

    else:

        cur.execute(
            """
            SELECT grant_id, 1 - d AS similarity
            FROM (
                SELECT
                    grant_id,
                    (embedding <=> %s::vector) AS d
                FROM GrantEmbeddings
                WHERE is_valid = TRUE
            ) ge
            WHERE d <= %s
            ORDER BY d
            LIMIT %s
            """,
            (
                query_vec_list,
                1 - similarity_threshold,
                max_results,
            )
        )

    return cur.fetchall()