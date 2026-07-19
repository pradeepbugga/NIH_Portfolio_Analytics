import argparse
import json
from pathlib import Path

from core.db.connection import get_db_connection

from core.llm.constants import CATEGORIES


def main():
    """
    This script imports classification results from JSONL files into the grant_labels table in the SQL database.
    Each JSONL file should contain records with grant_id and answer fields.
    The script will create the grant_labels table if it does not exist, and will insert or update records based on the grant_id.
    """

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--classification-dir",
        type=Path,
        required=True,
        help="Root directory containing all classification results.",
    )

    args = parser.parse_args()

    classification_dir = args.classification_dir

    # -------------------------
    # Load all category outputs
    # -------------------------

    master = {}

    for category in CATEGORIES:

        jsonl_path = classification_dir / category / "combined_results.jsonl"

        if not jsonl_path.exists():
            raise FileNotFoundError(jsonl_path)

        print(f"Loading {jsonl_path}")

        with jsonl_path.open() as f:

            for line in f:

                record = json.loads(line)

                grant_id = record["grant_id"]

                answer = record["answer"].strip().upper()

                master.setdefault(grant_id, {})

                master[grant_id][category] = answer == "YES"

    # -------------------------
    # Build rows
    # -------------------------

    rows = []

    for grant_id, labels in master.items():

        rows.append(
            (
                grant_id,
                int(labels.get("mechanistic", False)),
                int(labels.get("therapeutic", False)),
                int(labels.get("diagnostic", False)),
                int(labels.get("research_tool", False)),
                int(labels.get("clinical", False)),
                int(labels.get("research_infrastructure", False)),
                int(labels.get("education", False)),
                int(labels.get("observational_epidemiology", False)),
            )
        )

    # -------------------------
    # Insert into database
    # -------------------------

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS grant_labels (

        grant_id TEXT PRIMARY KEY,

        mechanistic INTEGER DEFAULT 0,
        therapeutic INTEGER DEFAULT 0,
        diagnostic INTEGER DEFAULT 0,
        research_tool INTEGER DEFAULT 0,
        clinical INTEGER DEFAULT 0,
        infrastructure INTEGER DEFAULT 0,
        education INTEGER DEFAULT 0,
        observational_epidemiology INTEGER DEFAULT 0
    );
    """)

    cur.executemany(
        """
        INSERT INTO grant_labels (

            grant_id,
            mechanistic,
            therapeutic,
            diagnostic,
            research_tool,
            clinical,
            infrastructure,
            education,
            observational_epidemiology

        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)

        ON CONFLICT (grant_id)
        DO UPDATE SET

            mechanistic = EXCLUDED.mechanistic,
            therapeutic = EXCLUDED.therapeutic,
            diagnostic = EXCLUDED.diagnostic,
            research_tool = EXCLUDED.research_tool,
            clinical = EXCLUDED.clinical,
            infrastructure = EXCLUDED.infrastructure,
            education = EXCLUDED.education,
            observational_epidemiology = EXCLUDED.observational_epidemiology;
        """,
        rows,
    )

    conn.commit()
    conn.close()

    print(f"Inserted {len(rows)} grants.")


if __name__ == "__main__":
    main()
