from unittest.mock import Mock, patch
import pytest

from core.ingest.persistence import (
    create_grant_embeddings_table,
    create_ingest_errors_table,
    create_ingest_runs_table,
    create_organizations_table,
    create_pis_table,
    create_research_grants_table,
    create_rgrant_pis_table,
    insert_organization,
    insert_research_grant,
    update_research_grant,
    insert_pis,
    insert_ingest_run,
    update_ingest_run_status,
    mark_ingest_run_failed,
    record_error,
    update_grant_embeddings,
)

# -----------------------------------
# TESTS for create_*_table functions
# -----------------------------------


@pytest.mark.parametrize(
    "func",
    [
        create_organizations_table,
        create_research_grants_table,
        create_pis_table,
        create_rgrant_pis_table,
        create_ingest_runs_table,
        create_ingest_errors_table,
        create_grant_embeddings_table,
    ],
)
def test_create_tables(func):
    """Test that the create_*_table functions execute the correct SQL to create the corresponding tables."""

    cur = Mock()

    func(cur)

    cur.execute.assert_called_once()

    sql = cur.execute.call_args.args[0]

    assert "CREATE TABLE IF NOT EXISTS" in sql


# -----------------------------------
# TESTS for insert_organization function
# -----------------------------------


def test_insert_organization_success():
    """Test that insert_organization inserts an organization into the database and returns the correct organization ID."""

    cur = Mock()

    cur.fetchone.return_value = (123,)

    org = {
        "name": "Harvard",
        "city": "Boston",
        "state": "MA",
        "country": "United States",
    }

    org_id = insert_organization(cur, org)

    assert cur.execute.call_count == 2
    assert org_id == 123


def test_insert_organization_existing():
    """Test that insert_organization returns the existing organization ID if the organization already exists in the database."""

    cur = Mock()

    cur.fetchone.return_value = (7,)

    org = {
        "name": "MIT",
        "city": "Cambridge",
        "state": "MA",
        "country": "United States",
    }

    org_id = insert_organization(cur, org)

    assert org_id == 7
    assert cur.execute.call_count == 2


def test_insert_organization_not_found():
    """Test that insert_organization raises a ValueError if the organization cannot be inserted or found in the database."""

    cur = Mock()

    cur.fetchone.return_value = None

    org = {
        "name": "Harvard",
        "city": "Boston",
        "state": "MA",
        "country": "United States",
    }

    with pytest.raises(
        ValueError,
        match="Failed to insert or find organization",
    ):
        insert_organization(cur, org)


def test_insert_organization_missing_fields():
    """Test that insert_organization handles missing organization fields by inserting empty strings for missing values."""

    cur = Mock()

    cur.fetchone.return_value = (5,)

    insert_organization(
        cur,
        {
            "name": None,
            "city": None,
            "state": None,
            "country": None,
        },
    )

    insert_args = cur.execute.call_args_list[0].args[1]

    assert insert_args == ("", "", "", "")


# -----------------------------------
# TESTS for insert_research_grant function
# -----------------------------------


def test_insert_research_grant():
    """Test that insert_research_grant inserts a research grant into the database with the correct parameters."""

    cur = Mock()

    result = {
        "project_num": "R01CA123456",
        "subproject_id": "1",
        "fiscal_year": 2025,
        "project_start_date": "2025-01-01T00:00:00",
        "project_end_date": "2029-12-31T00:00:00",
        "budget_start": "2025-01-01T00:00:00",
        "budget_end": "2026-01-01T00:00:00",
        "contact_pi_name": "john smith",
        "project_title": "Cancer Biology",
        "abstract_text": "Abstract",
        "phr_text": "PHR",
        "agency_ic_admin": {"name": "NCI"},
        "award_amount": 100000,
    }

    insert_research_grant(
        cur,
        result,
        core_project_num="R01CA123456",
        org_id=5,
        org_resolution_status="payload",
        ingest_id="abc",
        content_hash="hash123",
    )

    cur.execute.assert_called_once()


def test_insert_research_grant_without_subproject():
    """Test that insert_research_grant correctly handles a research grant without a subproject ID."""

    cur = Mock()

    result = {
        "project_num": "R01CA123456",
        "subproject_id": None,
        "fiscal_year": 2025,
        "budget_end": "2026-01-01T00:00:00",
        "agency_ic_admin": {"name": "NCI"},
    }

    insert_research_grant(
        cur,
        result,
        core_project_num="R01CA123456",
        org_id=1,
        org_resolution_status="payload",
        ingest_id="abc",
        content_hash="hash",
    )

    params = cur.execute.call_args.args[1]

    assert params[0] == "R01CA123456"


def test_insert_research_grant_strips_dates():
    """Test that insert_research_grant correctly strips the time portion from date fields before inserting into the database."""

    cur = Mock()

    result = {
        "project_num": "R01",
        "subproject_id": None,
        "fiscal_year": 2025,
        "project_start_date": "2025-05-03T15:41:22",
        "project_end_date": "2028-01-10T08:00:00",
        "budget_start": "2025-06-01T09:12:00",
        "budget_end": "2026-06-01T09:12:00",
        "agency_ic_admin": {"name": "NCI"},
    }

    insert_research_grant(
        cur,
        result,
        "R01",
        1,
        "payload",
        "run1",
        "hash",
    )

    params = cur.execute.call_args.args[1]

    assert params[7] == "2025-05-03"
    assert params[8] == "2028-01-10"
    assert params[9] == "2025-06-01"
    assert params[10] == "2026-06-01"


# -----------------------------------
# TESTS for update_research_grant function
# -----------------------------------


def test_update_research_grant():
    """Test that update_research_grant updates the research grant record with new values and increments the record version."""

    cur = Mock()

    result = {
        "project_title": "New title",
        "abstract_text": "Abstract",
        "phr_text": "PHR",
        "award_amount": 250000,
        "project_num": "R01CA123456",
        "subproject_id": "1",
    }

    update_research_grant(
        cur,
        result,
        grant_id="ignored",
        ingest_id="run1",
        content_hash="hash123",
        record_version=3,
    )

    cur.execute.assert_called_once()

    params = cur.execute.call_args.args[1]

    assert params[0] == "New title"
    assert params[4] == "hash123"
    assert params[5] == 4
    assert params[6] == "run1"


#  ------------------------------------
#  TESTS for insert_pis function
#  ------------------------------------


@patch("core.ingest.persistence.normalize_name")
def test_insert_pis_single(mock_normalize):
    """Test that insert_pis correctly inserts a single PI into the database and links them to the research grant."""

    cur = Mock()

    mock_normalize.return_value = (
        "John",
        "A",
        "Smith",
        "Smith, J",
    )

    cur.fetchone.return_value = (17,)

    pis = [
        {
            "full_name": "John A Smith",
            "is_contact_pi": True,
        }
    ]

    insert_pis(cur, "R01CA123456", pis)

    assert mock_normalize.call_count == 1
    assert cur.execute.call_count == 2


@patch("core.ingest.persistence.normalize_name")
def test_insert_pis_multiple(mock_normalize):
    """Test that insert_pis correctly inserts multiple PIs into the database and links them to the research grant."""

    cur = Mock()

    mock_normalize.side_effect = [
        ("John", "", "Smith", "Smith, J"),
        ("Jane", "", "Doe", "Doe, J"),
    ]

    cur.fetchone.side_effect = [
        (1,),
        (2,),
    ]

    pis = [
        {
            "full_name": "John Smith",
            "is_contact_pi": True,
        },
        {
            "full_name": "Jane Doe",
            "is_contact_pi": False,
        },
    ]

    insert_pis(cur, "R01CA123456", pis)

    assert mock_normalize.call_count == 2
    assert cur.execute.call_count == 4


@patch("core.ingest.persistence.normalize_name")
def test_insert_pis_contact_pi_flag(mock_normalize):
    """Test that insert_pis correctly sets the is_contact_pi flag for each PI when inserting into the RGrantPIs table."""

    cur = Mock()

    mock_normalize.return_value = (
        "John",
        "",
        "Smith",
        "Smith, J",
    )

    cur.fetchone.return_value = (42,)

    pis = [
        {
            "full_name": "John Smith",
            "is_contact_pi": False,
        }
    ]

    insert_pis(cur, "R01CA123456", pis)

    # Second execute() inserts into RGrantPIs
    params = cur.execute.call_args_list[1].args[1]

    assert params == (
        "R01CA123456",
        42,
        False,
    )


# ------------------------------------
# TESTS for insert_ingest_run function
# ------------------------------------


def test_insert_ingest_run():
    """Test that insert_ingest_run inserts a new ingest run record into the database with the correct parameters."""

    cur = Mock()

    insert_ingest_run(
        cur,
        ingest_id="run123",
    )

    cur.execute.assert_called_once()

    params = cur.execute.call_args.args[1]

    assert params == ("run123",)


# ------------------------------------
# TESTS for update_ingest_run_status function
# ------------------------------------


def test_update_ingest_run_status():
    """Test that update_ingest_run_status updates the ingest run record with the correct metrics."""

    cur = Mock()

    metrics = {
        "num_inserted": 10,
        "num_updated": 5,
        "num_skipped": 2,
        "num_errors": 1,
    }

    update_ingest_run_status(
        cur,
        ingest_id="run123",
        metrics=metrics,
    )

    cur.execute.assert_called_once()

    params = cur.execute.call_args.args[1]

    assert params == (
        10,
        5,
        2,
        1,
        "run123",
    )


# ------------------------------------
# TESTS for mark_ingest_run_failed function
# ------------------------------------


def test_mark_ingest_run_failed():
    """Test that mark_ingest_run_failed updates the ingest run record with the error message and sets the status to 'failed'."""

    cur = Mock()

    mark_ingest_run_failed(
        cur,
        ingest_id="run123",
        error_message="Database connection failed",
    )

    cur.execute.assert_called_once()

    params = cur.execute.call_args.args[1]

    assert params == (
        "Database connection failed",
        "run123",
    )


# ------------------------------------
# TESTS for mark_ingest_run_failed truncating long error messages
# ------------------------------------


def test_mark_ingest_run_failed_truncates_message():

    cur = Mock()

    error = "x" * 1500

    mark_ingest_run_failed(
        cur,
        ingest_id="run123",
        error_message=error,
    )

    params = cur.execute.call_args.args[1]

    assert len(params[0]) == 1000
    assert params[1] == "run123"


# ------------------------------------
# TESTS for record_error function
# ------------------------------------


def test_record_error():

    cur = Mock()

    record_error(
        cur,
        ingest_id="run123",
        grant_id="R01CA123456",
        error_type="ValueError",
        message="Missing organization",
    )

    cur.execute.assert_called_once()

    params = cur.execute.call_args.args[1]

    assert params == (
        "run123",
        "R01CA123456",
        "ValueError",
        "Missing organization",
    )


# ------------------------------------
# TESTS for update_grant_embeddings function
# ------------------------------------


def test_update_grant_embeddings():

    cur = Mock()

    update_grant_embeddings(
        cur,
        grant_id="R01CA123456",
    )

    cur.execute.assert_called_once()

    params = cur.execute.call_args.args[1]

    assert params == ("R01CA123456",)
