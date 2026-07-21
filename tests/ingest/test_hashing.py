from core.ingest.hashing import compute_content_hash, fetch_existing_hash
from unittest.mock import Mock


def test_compute_content_hash_deterministic():
    """Tests that compute_content_hash returns the same hash for the same content."""

    result = {
        "project_title": "Title",
        "abstract_text": "Abstract",
        "phr_text": "PHR",
        "award_amount": 100000,
    }

    hash1 = compute_content_hash(result)
    hash2 = compute_content_hash(result)

    assert hash1 == hash2


def test_compute_content_hash_changes_when_content_changes():
    """Tests that compute_content_hash returns different hashes when the content changes."""

    result1 = {
        "project_title": "Title",
        "abstract_text": "Abstract",
        "phr_text": "PHR",
        "award_amount": 100000,
    }

    result2 = {
        "project_title": "Different Title",
        "abstract_text": "Abstract",
        "phr_text": "PHR",
        "award_amount": 100000,
    }

    assert compute_content_hash(result1) != compute_content_hash(result2)


def test_compute_content_hash_missing_fields():
    """Tests that compute_content_hash handles missing fields gracefully by treating them as empty or zero values."""

    result = {}

    content_hash = compute_content_hash(result)

    assert isinstance(content_hash, str)

    assert len(content_hash) == 64


def test_fetch_existing_hash_found():
    """Tests that fetch_existing_hash correctly retrieves the existing hash and version when the grant exists in the database."""

    cur = Mock()

    cur.fetchone.return_value = (
        "abc123",
        4,
    )

    grant_id, row = fetch_existing_hash(
        cur,
        {
            "project_num": "R01CA123456",
            "subproject_id": "01",
        },
    )

    cur.execute.assert_called_once()

    assert grant_id == "R01CA123456-01"

    assert row == (
        "abc123",
        4,
    )


def test_fetch_existing_hash_without_subproject():
    """Tests that fetch_existing_hash correctly constructs the grant ID when subproject_id is missing."""

    cur = Mock()

    cur.fetchone.return_value = None

    grant_id, row = fetch_existing_hash(
        cur,
        {
            "project_num": "1R01CA123456-01",
            "subproject_id": None,
        },
    )

    assert grant_id == "1R01CA123456-01"

    assert row is None


def test_fetch_existing_hash_queries_expected_grant_id():
    """Tests that fetch_existing_hash executes the expected SQL query with the correct grant ID."""

    cur = Mock()

    cur.fetchone.return_value = None

    fetch_existing_hash(
        cur,
        {
            "project_num": "1R01CA123456",
            "subproject_id": "02",
        },
    )

    sql = cur.execute.call_args[0][0]

    params = cur.execute.call_args[0][1]

    assert "ResearchGrants" in sql

    assert params == ("1R01CA123456-02",)
