
async def fetch_grant_abstract(grant_id: str)-> dict:

    """
    Fetches the abstract for a given grant ID from the database.
    
    Parameters:
    ----------
    grant_id : str
        The unique identifier for the grant whose abstract is to be fetched.
    
    Returns:
    -------
    dict
        A dictionary containing the abstract of the grant. If the grant is not found, raises a ValueError.
    """


    conn = await anyio.to_thread.run_sync(get_db_connection)
    cur = conn.cursor()

    try:

        def fetch():

            cur.execute(
                """
                SELECT abstract
                FROM ResearchGrants
                WHERE grant_id = %s
                """,
                (grant_id,),
            )

            return cur.fetchone()

        row = await anyio.to_thread.run_sync(fetch)

        if row is None:
            raise ValueError("Grant not found.")

        return {
            "abstract": row[0] or "No abstract available for this record."
        }

    finally:

        await anyio.to_thread.run_sync(cur.close)
        await anyio.to_thread.run_sync(conn.close)

