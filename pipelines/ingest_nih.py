#this script runs the NIH grant data ingestion pipeline for the specified fiscal years

import json
from datetime import datetime

from core.db.connection import get_db_connection, DB_PATH
from core.ingest.ingest import ingest_year
from core.ingest.persistence import insert_ingest_run, update_ingest_run_status, mark_ingest_run_failed, create_ingest_errors_table
from core.ingest.persistence import create_organizations_table, create_research_grants_table, create_pis_table, create_rgrant_pis_table, create_ingest_runs_table, create_grant_embeddings_table

import os
from core.ingest.config import IngestMode, ingest_policy, current_fiscal_year, years_to_ingest
import traceback


CACHE_PATH = './data/org_fix_cache.json'

raw_mode = os.getenv("APP_MODE", "production")

INGEST_MODE = IngestMode(raw_mode)
POLICY = ingest_policy(INGEST_MODE)

years = years_to_ingest(INGEST_MODE)

def load_cache():
    try:
        with open(CACHE_PATH, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_cache(cache):
    with open(CACHE_PATH, 'w') as f:
        json.dump(cache, f, indent=2)


if __name__ == "__main__":
    
    conn = get_db_connection()
    
    org_cache = load_cache()

    ingest_id = f"nih_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}"
    print(ingest_id)

    metrics = {
        "num_inserted": 0,
        "num_updated": 0,
        "num_skipped": 0,
        "num_errors": 0}  

    cur = conn.cursor()
    create_organizations_table(cur)
    create_research_grants_table(cur)
    create_pis_table(cur)
    create_rgrant_pis_table(cur)
    create_ingest_runs_table(cur)
    create_grant_embeddings_table(cur)
    create_ingest_errors_table(cur)
    conn.commit()

    try: 
        insert_ingest_run(cur, ingest_id)
        print("Ingest run record created.")
        for year in years:
            ingest_year(year, conn, cur, org_cache, ingest_id, POLICY, metrics)
            save_cache(org_cache)
        
        update_ingest_run_status(cur, ingest_id, metrics)

        conn.commit()
        print("Ingest completed successfully.")
    except Exception as e:
        print("Ingest failed:", e)
        traceback.print_exc()
        conn.rollback()
        mark_ingest_run_failed(cur, ingest_id, error_message=str(e))
        conn.commit()
        raise

    finally:
        cur.close()
        conn.close()
        