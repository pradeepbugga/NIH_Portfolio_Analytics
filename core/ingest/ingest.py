#ingest.py
#this script ingests NIH grant data for a given fiscal year, normalizes it, and stores it in a database

import json
import time
from core.ingest.normalize import normalize_project_num
from core.ingest.reporter_client import API_URL, PAGE_LIMIT, SLEEP_SECONDS, AGENCIES, MAX_RETRIES
from core.ingest.reporter_client import fetch_projects, build_payload, backoff
from core.ingest.process import process_result
from tqdm import tqdm
from core.ingest.persistence import record_error
import requests

class DataQualityError(Exception):
    pass

def ingest_year(year:int, conn, cur, org_cache:dict, ingest_id:str, POLICY:dict, metrics:dict):

    """
    Ingests NIH grant data for a given fiscal year, normalizes it, and stores it in a database.

    Parameters
    ----------
    year (int): The fiscal year for which to ingest NIH grant data.
    conn: A database connection object for executing SQL queries.
    cur: A database cursor for executing SQL queries.
    org_cache (dict): A cache of organization information to avoid redundant API calls.
    ingest_id (str): A unique identifier for the current ingestion process.
    POLICY (dict): A dictionary containing policy settings for organization resolution.
    metrics (dict): A dictionary to track metrics such as the number of inserted, updated, skipped, and errored records.

    Raises
    ------
    RuntimeError: If the NIH API is unavailable after the maximum number of retries.
    
    """
    

    for agency in AGENCIES:
        offset=0
        search_id = None
        total = float('inf')
        pbar = None
        
        while(offset<total):
            payload = build_payload(year, agency, offset, search_id)
            data = None
            for attempt in range(MAX_RETRIES+1):
                try:  
                    data = fetch_projects(payload)
                    break
                except requests.RequestException as e:
                    if attempt == MAX_RETRIES:
                        raise RuntimeError(f"NIH API unavailable after {MAX_RETRIES} retries " f"(FY={year}, agency={agency}, offset={offset})")
                    time.sleep(backoff(attempt))

            if pbar is None:
                search_id = data.get("search_id")
                if data.get("meta") and "total" in data["meta"]:
                    total = data["meta"]["total"]
                pbar = tqdm(total=total, desc=f"FY{year} {agency}", unit="grants")
            for result in data.get("results", []):
                try:    
                    process_result(result, cur, org_cache, ingest_id, POLICY, metrics)
                    pbar.update(1)
                except DataQualityError as e:
                    conn.rollback()
                    grant_id = f"{result.get('project_num')}-{result.get('subproject_id')}" if result.get('subproject_id') else result.get('project_num')
                    record_error(cur, grant_id, ingest_id, type(e).__name__, str(e))
                    metrics["num_errors"] += 1
                    continue
                
                    
            
            offset += PAGE_LIMIT
            time.sleep(SLEEP_SECONDS)

        if pbar:
            pbar.close()
