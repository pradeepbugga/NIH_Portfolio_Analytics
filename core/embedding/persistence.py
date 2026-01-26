#this script contains functions for persisting grant embeddings to the database

#this function inserts or updates a grant embedding in the database
def upsert_embedding(cur, grant_id, content_hash, cfg, vector):
    cur.execute(
        """
        INSERT INTO GrantEmbeddings
            (grant_id, content_hash, embedding_model,
             text_recipe, normalization, embedding_version,
             embedding, is_valid)
        VALUES (%s, %s, %s, %s, %s, %s, %s, TRUE)
        ON CONFLICT (grant_id)
        DO UPDATE SET
            content_hash = EXCLUDED.content_hash,
            embedding_model = EXCLUDED.embedding_model,
            text_recipe = EXCLUDED.text_recipe,
            normalization = EXCLUDED.normalization,
            embedding_version = EXCLUDED.embedding_version,
            embedding = EXCLUDED.embedding,
            is_valid = TRUE,
            created_at = CURRENT_TIMESTAMP
        """,
        (
            grant_id,
            content_hash,
            cfg.model_name,
            cfg.text_recipe,
            cfg.normalization,
            cfg.embedding_version,
            vector.tolist(),
        )
    )

#this function counts the number of grants that need to be embedded
def count_grants_to_embed(cur) -> int:
    cur.execute(
        """
        SELECT COUNT(*)
        FROM ResearchGrants rg
        LEFT JOIN GrantEmbeddings ge
          ON rg.grant_id = ge.grant_id
        WHERE rg.project_title IS NOT NULL
          AND rg.abstract IS NOT NULL
          
          AND (
                ge.grant_id IS NULL
             OR ge.is_valid = FALSE
             OR ge.content_hash <> rg.content_hash
          )
        """
    )
    return cur.fetchone()[0]