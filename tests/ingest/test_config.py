from datetime import datetime
import pytest
from core.ingest.config import ingest_policy, current_fiscal_year, years_to_ingest, IngestMode


def test_ingest_policy_historical():

    """ Tests that ingest_policy returns the correct settings for HISTORICAL mode. """

    policy = ingest_policy(
        IngestMode.HISTORICAL,
    )

    assert policy == {
        "allow_future_lookup": True,
        "allow_manual_lookup": True,
        "fail_on_missing_org": False,
        "require_hash": False,
    }

def test_ingest_policy_production():

    """ Tests that ingest_policy returns the correct settings for PRODUCTION mode. """

    policy = ingest_policy(
        IngestMode.PRODUCTION,
    )

    assert policy == {
        "allow_future_lookup": False,
        "allow_manual_lookup": False,
        "fail_on_missing_org": False,
        "require_hash": True,
    }

def test_current_fiscal_year_before_october():

    """ Tests that current_fiscal_year returns the current calendar year when the month is before October. """

    fy = current_fiscal_year(
        datetime(2025, 9, 30),
    )

    assert fy == 2025

def test_current_fiscal_year_october():

    """ Tests that current_fiscal_year returns the next calendar year when the month is October or later. """

    fy = current_fiscal_year(
        datetime(2025, 10, 1),
    )

    assert fy == 2026

def test_years_to_ingest_production():

    """ Tests that years_to_ingest returns the correct list of fiscal years for PRODUCTION mode. """

    years = years_to_ingest(
        IngestMode.PRODUCTION,
        datetime(2025, 11, 1),
    )

    assert years == [
        2026,
        2025,
    ]

def test_years_to_ingest_historical():

    """ Tests that years_to_ingest returns the correct list of fiscal years for HISTORICAL mode. """

    years = years_to_ingest(
        IngestMode.HISTORICAL,
        datetime(2025, 11, 1),
    )

    assert years[0] == 1985

    assert years[-1] == 2026

    assert len(years) == 42


def test_years_to_ingest_invalid_mode():

    """ Tests that years_to_ingest raises a ValueError when given an invalid mode. """

    with pytest.raises(ValueError):

        years_to_ingest(
            "bad_mode",
        )