# this script runs the NIH grant data ingestion pipeline for the specified fiscal years

import json
from datetime import datetime, timezone

import logging
from core.logging_config import configure_logging

from core.db.connection import get_db_connection
from core.ingest.ingest import ingest_year
from core.ingest.persistence import (
    insert_ingest_run,
    update_ingest_run_status,
    mark_ingest_run_failed,
    create_ingest_errors_table,
)
from core.ingest.persistence import (
    create_organizations_table,
    create_research_grants_table,
    create_pis_table,
    create_rgrant_pis_table,
    create_ingest_runs_table,
    create_grant_embeddings_table,
)

import os
from core.ingest.config import (
    IngestMode,
    ingest_policy,
    years_to_ingest,
)

logger = logging.getLogger(__name__)

CACHE_PATH = "./data/org_fix_cache.json"

raw_mode = os.getenv("APP_MODE", "production")

INGEST_MODE = IngestMode(raw_mode)
POLICY = ingest_policy(INGEST_MODE)

years = years_to_ingest(INGEST_MODE)


def load_cache():
    try:
        with open(CACHE_PATH, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def save_cache(cache):
    with open(CACHE_PATH, "w") as f:
        json.dump(cache, f, indent=2)


def main():
    configure_logging()

    logger.info("Starting NIH grant data ingestion pipeline (mode=%s)", INGEST_MODE)

    conn = get_db_connection()

    org_cache = load_cache()

    logger.info("Loaded organization fix cache with %d entries.", len(org_cache))

    ingest_id = f"nih_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}"
    logger.info("Starting ingest run with ID: %s", ingest_id)

    metrics = {"num_inserted": 0, "num_updated": 0, "num_skipped": 0, "num_errors": 0}

    cur = conn.cursor()
    create_organizations_table(cur)
    create_research_grants_table(cur)
    create_pis_table(cur)
    create_rgrant_pis_table(cur)
    create_ingest_runs_table(cur)
    create_grant_embeddings_table(cur)
    create_ingest_errors_table(cur)
    conn.commit()

    logger.info("Database schema verified.")

    try:
        insert_ingest_run(cur, ingest_id)
        logger.info("Ingest run record created.")

        for year in years:
            logger.info("Starting ingestion for fiscal year: %d", year)

            ingest_year(year, conn, cur, org_cache, ingest_id, POLICY, metrics)

            logger.info("Completed ingestion for fiscal year: %d", year)

            save_cache(org_cache)

        update_ingest_run_status(cur, ingest_id, metrics)

        logger.info(
            "Ingest metrics: inserted=%d updated=%d skipped=%d errors=%d",
            metrics["num_inserted"],
            metrics["num_updated"],
            metrics["num_skipped"],
            metrics["num_errors"],
        )

        conn.commit()
        logger.info("Ingest run completed successfully.")

    except Exception as e:

        logger.exception("Ingest failed.")
        conn.rollback()
        mark_ingest_run_failed(cur, ingest_id, error_message=str(e))
        conn.commit()
        raise

    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()
