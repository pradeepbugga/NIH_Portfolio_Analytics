def load_grant_texts(cur, grant_ids):
    """
    Load grant texts from the database for the given grant IDs.

    Returns
    -------
    dict
        {
            grant_id: {
                "title": ...,
                "abstract": ...
            }
        }
    """

    cur.execute(
        """
        SELECT grant_id, project_title, abstract
        FROM researchgrants
        WHERE grant_id = ANY(%s)
        """,
        (grant_ids,),
    )

    return {
        grant_id: {
            "title": title,
            "abstract": abstract,
        }
        for grant_id, title, abstract in cur.fetchall()
    }
