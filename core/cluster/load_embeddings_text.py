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
            rg.agency_code,
            o.state,
            ge.embedding,
            gl.mechanistic,
            gl.therapeutic,
            gl.diagnostic,
            gl.research_tool,
            gl.clinical,
            gl.infrastructure,
            gl.education,
            gl.obs_ep
        FROM ResearchGrants rg
        JOIN grant_labels gl ON rg.grant_id = gl.grant_id
        INNER JOIN GrantEmbeddings ge ON rg.grant_id = ge.grant_id
        LEFT JOIN organizations o ON rg.organization_id = o.id
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

        _, title, abstract, amount, agency_code, org_state, embedding, mechanistic, therapeutic, diagnostic, research_tool, clinical, infrastructure, education, obs_ep = row_map[gid]

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
            "agency_code": agency_code,
            "org_state": org_state,
            "embedding": embedding,
            "mechanistic": mechanistic,
            "therapeutic": therapeutic,
            "diagnostic": diagnostic,
            "research_tool": research_tool,
            "clinical": clinical,
            "infrastructure": infrastructure,
            "education": education,
            "obs_ep": obs_ep
        })

    return docs