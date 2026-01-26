# this script contains functions for selecting grants that need to be embedded

def stream_grants_to_embed(cur):
    cur.execute(
        """
        SELECT
            rg.grant_id,
            rg.project_title,
            rg.abstract,
            rg.content_hash
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