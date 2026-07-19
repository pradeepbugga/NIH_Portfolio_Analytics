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


def upsert_summary_embedding(cur, grant_id, content_hash, cfg, vector):
    """
    Inserts or updates a summary embedding in its dedicated table.
    """
    cur.execute(
        """
        INSERT INTO GrantSummaryEmbeddings
            (grant_id, content_hash, embedding_model,
             text_recipe, normalization, embedding_version,
             embedding, is_valid)
        VALUES (%s, %s, %s, %s, %s, %s, %s, TRUE)
        ON CONFLICT (grant_id) 
        DO UPDATE SET
            content_hash = EXCLUDED.content_hash,
            embedding_model = EXCLUDED.embedding_model,
            text_recipe = EXCLUDED.text_recipe,
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

def count_summaries_to_embed(cur) -> int:
    """
    Counts remaining summaries left to process.
    """
    cur.execute(
        """
        SELECT COUNT(*)
        FROM grant_summaries gs
        LEFT JOIN GrantSummaryEmbeddings gse
          ON gs.grant_id = gse.grant_id
        WHERE gs.two_sentence_summary IS NOT NULL
          AND (
                gse.grant_id IS NULL
             OR gse.is_valid = FALSE
             OR gse.content_hash <> MD5(gs.two_sentence_summary)
          )
        """
    )
    return cur.fetchone()[0]