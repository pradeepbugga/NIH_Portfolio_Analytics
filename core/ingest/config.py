from enum import Enum
from datetime import datetime


class IngestMode(str, Enum):
    HISTORICAL = (
        "historical_backfill"  # backfill is for ingesting historical NIH grant data
    )
    PRODUCTION = "production"  # prodction is forward-looking and for ingesting current and future NIH grant data


def ingest_policy(mode: IngestMode) -> dict:
    """
    Get the ingestion policy based on the specified mode.

    Parameters
    ----------

    mode (IngestMode): The ingestion mode, either HISTORICAL or PRODUCTION.

    Returns
    -------
    dict: A dictionary containing the ingestion policy settings.
    """

    return {
        "allow_future_lookup": mode == IngestMode.HISTORICAL,
        "allow_manual_lookup": mode == IngestMode.HISTORICAL,
        "fail_on_missing_org": False,
        "require_hash": mode == IngestMode.PRODUCTION,
    }


def current_fiscal_year(dt=None):
    """
    Get the current fiscal year based on the provided datetime or the current UTC time.

    Parameters
    ----------
    dt (datetime, optional): A datetime object to determine the fiscal year. If None, the current UTC time is used.

    Returns
    -------
    int: The current fiscal year. If the month is October or later, the fiscal year is the next calendar year; otherwise, it is the current calendar year.
    """

    if dt is None:
        dt = datetime.utcnow()
    return dt.year + 1 if dt.month >= 10 else dt.year


def years_to_ingest(mode: IngestMode, now=None):
    """
    Get the list of fiscal years to ingest based on the specified mode.

    Parameters
    ----------

    mode (IngestMode): The ingestion mode, either HISTORICAL or PRODUCTION.
    now (datetime, optional): A datetime object to determine the current fiscal year. If None, the current UTC time is used.

    Returns
    -------
    list: A list of fiscal years to ingest. For PRODUCTION mode, it returns the current and previous fiscal years. For HISTORICAL mode, it returns all fiscal years from 1985 to the current fiscal year.
    """

    fy = current_fiscal_year(now)

    if mode == IngestMode.PRODUCTION:
        return [fy, fy - 1]

    if mode == IngestMode.HISTORICAL:
        return list(range(1985, fy + 1))

    raise ValueError(f"Unknown ingest mode: {mode}")
