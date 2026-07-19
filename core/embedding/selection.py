def stream_grants_to_embed(cur):
    """
    Streams grants from ResearchGrants that lack an up-to-date embedding in the GrantEmbeddings table.
    """

    cur.execute("""
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
        """)


def stream_summaries_to_embed(cur):
    """
    Streams summaries from grant_summaries that lack an up-to-date
    embedding in the GrantSummaryEmbeddings table.
    """
    cur.execute("""
        SELECT
            gs.grant_id,
            gs.two_sentence_summary,
            MD5(gs.two_sentence_summary) AS content_hash
        FROM grant_summaries gs
        LEFT JOIN GrantSummaryEmbeddings gse
          ON gs.grant_id = gse.grant_id
        WHERE gs.two_sentence_summary IS NOT NULL
          AND (
                gse.grant_id IS NULL
             OR gse.is_valid = FALSE
             OR gse.content_hash <> MD5(gs.two_sentence_summary)
          )
        """)
