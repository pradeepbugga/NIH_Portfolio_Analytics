def load_grant_embeddings_and_text(cur, grant_ids):
    if not grant_ids:
        return []

    cur.execute(
        """
        SELECT 
            rg.grant_id,
            rg.project_title,
            rg.abstract,
            rg.total_award_amount,
            ge.embedding
        FROM ResearchGrants rg
        INNER JOIN GrantEmbeddings ge ON rg.grant_id = ge.grant_id
        WHERE rg.grant_id = ANY(%s)
        """,
        (grant_ids,)
    )

    rows = cur.fetchall()
    row_map = {r[0]: r for r in rows}

    docs = []
    # Loop over the user's provided list to preserve their filtered order
    for gid in grant_ids:
        if gid not in row_map:
            continue

        _, title, abstract, amount, embedding = row_map[gid]

        # Convert embedding back into a usable NumPy float array if stored as text/binary
        # (Skip this conversion step if your DB driver returns it as a list of floats natively)
        if isinstance(embedding, str):
            import json
            embedding = json.loads(embedding)

        docs.append({
            "grant_id": gid,
            "title": title,
            "abstract": abstract,
            "amount": amount,
            "embedding": embedding
        })

    return docs