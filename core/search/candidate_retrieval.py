# this script retrieves candidate NIH grants based on embedding similarity
# you can use either top-k or range-based retrieval (latter preferred for our high recall application)

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
def retrieve_candidates_range(cur, query_vec_list, similarity_threshold, max_results=500000):
    
     
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

