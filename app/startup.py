from contextlib import asynccontextmanager
import os
import json

from fastapi import FastAPI

import pandas as pd

from core.search.query_embedding import warmup_query_encoder

# Global placeholders for static reference data (initialized once at startup)
GLOBAL_AGENCIES_LIST = []
GLOBAL_VALID_ACTIVITY_CODES = []
GLOBAL_SYNONYM_REGISTRY = {}


# ================================================================
# STARTUP LIFESPAN MANAGEMENT (runs exactly once on server boot)
# ================================================================
@asynccontextmanager
async def application_lifespan(app: FastAPI):
    """
    Handles critical initialization protocols before ports are opened to traffic.
    This includes loading ML encoder and parsing static reference datasets for agencies and activity codes.
    This also includes loading synonym mappings for query expansion.
    """
    global GLOBAL_AGENCIES_LIST, GLOBAL_VALID_ACTIVITY_CODES, GLOBAL_SYNONYM_REGISTRY
    print("Running global application warmups...")

    # 1. Warmup the local query encoder (PubmedBERT) to avoid cold-start latency on first query
    warmup_query_encoder()

    # 2. Pre-cache reference dataset csv metrics to prevent repeated disk reads on every request
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # map and load agency data
    csv_path = os.path.abspath(
        os.path.join(script_dir, "..", "data", "agencies_list.csv")
    )
    if os.path.exists(csv_path):
        try:
            df = pd.read_csv(csv_path).fillna("")
            GLOBAL_AGENCIES_LIST = df.sort_values(by="agency_ic").to_dict(
                orient="records"
            )
            print(f"✅ Cached {len(GLOBAL_AGENCIES_LIST)} agency mapping matrices.")
        except Exception as e:
            print(f"❌ ERROR reading/parsing agency CSV: {e}")

    # map and load activity code data
    activity_csv_path = os.path.abspath(
        os.path.join(script_dir, "..", "data", "activity_code_list.csv")
    )
    if os.path.exists(activity_csv_path):
        try:
            df_activity = pd.read_csv(activity_csv_path)
            GLOBAL_VALID_ACTIVITY_CODES = (
                df_activity["Activity_Code"].str.upper().tolist()
            )
            print(
                f"✅ Cached {len(GLOBAL_VALID_ACTIVITY_CODES)} valid global structural activity codes."
            )
        except Exception as e:
            print(f"❌ ERROR reading/parsing activity codes CSV: {e}")

    print("Warmups complete. Application is ready to serve requests.")

    # map and load synonym registry for query expansion
    synonym_json_path = os.path.abspath(
        os.path.join(script_dir, "..", "data", "rcdc_synonyms.json")
    )
    if os.path.exists(synonym_json_path):
        try:
            with open(synonym_json_path, "r") as f:
                GLOBAL_SYNONYM_REGISTRY = json.load(f)
            print(
                f"✅ Cached {len(GLOBAL_SYNONYM_REGISTRY)} domain synonym expansion targets into memory."
            )
        except Exception as e:
            print(f"❌ ERROR reading/parsing synonym JSON: {e}")
            GLOBAL_SYNONYM_REGISTRY = {}
    else:
        print(f"⚠️ Warning: Synonym map not found at {synonym_json_path}")

    yield
