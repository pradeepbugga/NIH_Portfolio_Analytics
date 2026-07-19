# this script fills in missing abstracts for labels CSV
# this is specifcally used with train_reranker 

import pandas as pd
from core.db.connection import get_db_connection


def add_abstracts(df: pd.DataFrame) -> pd.DataFrame:

    """
    Add abstracts to a DataFrame containing grant IDs by querying the database.

    Parameters
    ----------
    df : pd.DataFrame
        A DataFrame containing a column named 'grant_id' with grant IDs.

    Returns
    -------
    pd.DataFrame
        The input DataFrame with an additional column named 'abstract' containing the corresponding abstracts.
    """
    


    grant_ids = df["grant_id"].unique().tolist()

    conn = get_db_connection()

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    grant_id,
                    abstract
                FROM ResearchGrants
                WHERE grant_id = ANY(%s)
                """,
                (grant_ids,)
            )

            rows = cur.fetchall()

    finally:
        conn.close()
        
    abstract_map = {grant_id: abstract for grant_id, abstract in rows}
    df["abstract"] = df["grant_id"].map(abstract_map)

    return df