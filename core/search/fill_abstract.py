# this script fills in missing abstracts for labels CSV
# this is specifcally used with train_reranker 

import pandas as pd
from core.db.connection import get_db_connection

conn = get_db_connection()
cur = conn.cursor()


def add_abstracts(df):
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