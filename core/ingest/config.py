# this script contains configuration settings for the NIH grant data ingestion process

from enum import Enum
from datetime import datetime

#backfill is for ingesting historical NIH grant data
#production is forward-looking 

class IngestMode(str, Enum):
    HISTORICAL = "historical_backfill"
    PRODUCTION = "production"
    
def ingest_policy(mode: IngestMode) -> dict:
    return {
        "allow_future_lookup": mode == IngestMode.HISTORICAL,
        "allow_manual_input": mode == IngestMode.HISTORICAL,
        "fail_on_missing_org": False,
        "require_hash": mode == IngestMode.PRODUCTION,}

def current_fiscal_year(dt=None):
    if dt is None:
        dt = datetime.utcnow()
    return dt.year + 1 if dt.month >= 10 else dt.year

def years_to_ingest(mode: IngestMode, now = None):
    fy = current_fiscal_year(now)

    if mode == IngestMode.PRODUCTION:
        return [fy, fy-1]
        
    
    if mode == IngestMode.HISTORICAL_BACKFILL:
        return list(range(1985, fy+1))
    
    raise ValueError(f"Unknown ingest mode: {mode}")