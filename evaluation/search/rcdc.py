import pandas as pd
from pathlib import Path
from core.db.connection import get_db_connection

GROUND_TRUTH_DIR = Path(__file__).parent / "ground_truth"


def load_rcdc_portfolio(category: str) -> pd.DataFrame:
    conn = get_db_connection()
    cur = conn.cursor()

    path = GROUND_TRUTH_DIR / f"{category}.csv"

    df = pd.read_csv(path)

    # Create your composite key matching grant_id from the format generated from my search service
    df["grant_id"] = df.apply(
        lambda row: (
            f"{row['Project Number']}-{row['Sub Project #']}"
            if pd.notna(row["Sub Project #"])
            else str(row["Project Number"])
        ),
        axis=1,
    )

    # drop duplicates based on the new grant_id column
    df = df.drop_duplicates(subset=["grant_id"])

    # drop null values in the grant_id column
    df = df[df["grant_id"].notnull()]

    # drop intramural grants (grant_id starting with "1ZIA")
    df = df[~df["grant_id"].astype(str).str.startswith("1ZIA")]

    # clean up the "Amount" column by removing "$" and "," and converting to float

    df["Amount"] = (
        df["Amount"]
        .str.replace("$", "", regex=False)
        .str.replace(",", "", regex=False)
        .astype(float)
    )

    try:
        # drop grants not in db (correct for any ingest errors)
        # note: once we ingest 100% of grants, we can remove this step
        cur.execute(
            """
            SELECT grant_id FROM researchgrants WHERE grant_id = ANY(%s)
            """,
            (df["grant_id"].astype(str).tolist(),),
        )
        existing_grant_ids = {row[0] for row in cur.fetchall()}

        df = df[df["grant_id"].isin(existing_grant_ids)]

        df = df.reset_index(drop=True)
    finally:
        cur.close()
        conn.close()

    return df
