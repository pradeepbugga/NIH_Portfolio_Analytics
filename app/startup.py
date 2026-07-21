from contextlib import asynccontextmanager
import os
import json

from fastapi import FastAPI
import logging

import pandas as pd

from core.search.query_embedding import warmup_query_encoder

# Global placeholders for static reference data (initialized once at startup)
GLOBAL_AGENCIES_LIST = []
GLOBAL_VALID_ACTIVITY_CODES = []
GLOBAL_SYNONYM_REGISTRY = {}

logger = logging.getLogger(__name__)

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
    logger.info("Starting application initialization...")
 
    # 1. Warmup the local query encoder (PubmedBERT) to avoid cold-start latency on first query
    try:
        logger.info("Warming up query encoder...")
        warmup_query_encoder()
        logger.info("Query encoder warmup complete. Proceeding to load static reference datasets...")
    except Exception:
        logger.exception("Failed to warmup query encoder.")
        raise
    
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
            logger.info("Loaded %d agency records.", len(GLOBAL_AGENCIES_LIST))
        except Exception:
            logger.exception(f"❌ Failed to load agency reference data")

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
            logger.info("✅ Loaded %d activity codes.", len(GLOBAL_VALID_ACTIVITY_CODES))  
        except Exception:
            logger.exception(f"❌ Failed to load activity code reference data")

    # map and load synonym registry for query expansion
    synonym_json_path = os.path.abspath(
        os.path.join(script_dir, "..", "data", "rcdc_synonyms.json")
    )
    if os.path.exists(synonym_json_path):
        try:
            with open(synonym_json_path, "r") as f:
                GLOBAL_SYNONYM_REGISTRY = json.load(f)
            logger.info("✅ Loaded %d query synonyms.", len(GLOBAL_SYNONYM_REGISTRY))
        except Exception:
            logger.exception(f"❌ Failed to load query synonyms.")
            GLOBAL_SYNONYM_REGISTRY = {}
    else:
        logger.warning("⚠️ Synonym registry not found: %s", synonym_json_path)

    logger.info("Application initialization complete.")

    yield
