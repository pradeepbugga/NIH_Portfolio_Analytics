import argparse
import json
from pathlib import Path

from core.db.connection import get_db_connection
from core.llm.constants import SUMMARY_MODEL, SUMMARY_REASONING

model_effort = SUMMARY_REASONING.get("effort", "N/A")

db_model_description = f"{SUMMARY_MODEL} {model_effort} effort reasoning"


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--summary-dir",
        type=Path,
        required=True,
        help="Directory containing parsed summary JSONL files.",
    )

    args = parser.parse_args()

    summary_dir = args.summary_dir

    parsed_files = sorted(summary_dir.glob("*_parsed.jsonl"))

    if not parsed_files:
        raise ValueError(f"No parsed summary files found in {summary_dir}")

    rows = []

    for path in parsed_files:

        print(f"Loading {path.name}")

        with path.open() as f:

            for line in f:

                record = json.loads(line)

                rows.append(
                    (record["grant_id"], record["summary"], db_model_description)
                )

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS grant_summaries (

        grant_id TEXT PRIMARY KEY,

        two_sentence_summary TEXT NOT NULL,

        summary_llm_model TEXT NOT NULL,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

    );
    """)

    cur.executemany(
        """
        INSERT INTO grant_summaries (

            grant_id,
            two_sentence_summary,
            summary_llm_model

        )
        VALUES (%s, %s, %s)

        ON CONFLICT (grant_id)

        DO UPDATE SET

            two_sentence_summary = EXCLUDED.two_sentence_summary,
            summary_llm_model = EXCLUDED.summary_llm_model,
            updated_at = CURRENT_TIMESTAMP;
        """,
        rows,
    )

    conn.commit()
    conn.close()

    print(f"Imported {len(rows)} summaries.")


if __name__ == "__main__":
    main()
