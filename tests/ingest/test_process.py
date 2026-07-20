from unittest.mock import patch, Mock
import pytest

from core.ingest.process import process_result


@patch("core.ingest.process.resolve_org")
@patch("core.ingest.process.normalize_project_num")
@patch("core.ingest.process.insert_pis")
@patch("core.ingest.process.update_grant_embeddings")
@patch("core.ingest.process.update_research_grant")
@patch("core.ingest.process.insert_research_grant")
@patch("core.ingest.process.insert_organization")
@patch("core.ingest.process.fetch_existing_hash")
@patch("core.ingest.process.compute_content_hash")
def test_process_result_insert(
    mock_compute_hash,
    mock_fetch_hash,
    mock_insert_org,
    mock_insert_grant,
    mock_update_grant,
    mock_update_embeddings,
    mock_insert_pis,
    mock_normalize,
    mock_resolve_org,
):
    """Test that process_result correctly inserts a new research grant when no existing hash is found."""

    mock_fetch_hash.return_value = (
        "R01CA123456",
        None,
    )
    mock_compute_hash.return_value = "hash123"
    mock_normalize.return_value = "R01CA123456"
    mock_resolve_org.return_value = ({"name": "Harvard"}, "payload")
    mock_insert_org.return_value = 7

    cur = Mock()

    result = {
        "project_num": "R01CA123456",
        "fiscal_year": 2025,
        "organization": {},
        "agency_ic_admin": {"abbreviation": "NCI"},
        "principal_investigators": [],
    }

    metrics = {
        "num_inserted": 0,
        "num_updated": 0,
        "num_skipped": 0,
    }

    process_result(
        result=result,
        cur=cur,
        org_cache={},
        ingest_id="run123",
        policy={},
        metrics=metrics,
    )

    mock_insert_grant.assert_called_once()
    mock_insert_pis.assert_called_once()

    mock_update_grant.assert_not_called()
    mock_update_embeddings.assert_not_called()

    assert metrics["num_inserted"] == 1
    assert metrics["num_updated"] == 0
    assert metrics["num_skipped"] == 0


@patch("core.ingest.process.resolve_org")
@patch("core.ingest.process.normalize_project_num")
@patch("core.ingest.process.insert_pis")
@patch("core.ingest.process.update_grant_embeddings")
@patch("core.ingest.process.update_research_grant")
@patch("core.ingest.process.insert_research_grant")
@patch("core.ingest.process.insert_organization")
@patch("core.ingest.process.fetch_existing_hash")
@patch("core.ingest.process.compute_content_hash")
def test_process_result_skip(
    mock_compute_hash,
    mock_fetch_hash,
    mock_insert_org,
    mock_insert_grant,
    mock_update_grant,
    mock_update_embeddings,
    mock_insert_pis,
    mock_normalize,
    mock_resolve_org,
):
    """Test that process_result correctly skips a research grant when the existing hash matches the computed hash."""

    mock_fetch_hash.return_value = (
        "R01CA123456",
        ("hash123", 2),
    )
    mock_compute_hash.return_value = "hash123"
    mock_normalize.return_value = "R01CA123456"
    mock_resolve_org.return_value = ({"name": "Harvard"}, "payload")
    mock_insert_org.return_value = 7

    cur = Mock()

    result = {
        "project_num": "R01CA123456",
        "fiscal_year": 2025,
        "organization": {},
        "agency_ic_admin": {"abbreviation": "NCI"},
        "principal_investigators": [],
    }

    metrics = {
        "num_inserted": 0,
        "num_updated": 0,
        "num_skipped": 0,
    }

    process_result(
        result=result,
        cur=cur,
        org_cache={},
        ingest_id="run123",
        policy={},
        metrics=metrics,
    )

    mock_insert_grant.assert_not_called()
    mock_update_grant.assert_not_called()
    mock_update_embeddings.assert_not_called()
    mock_insert_pis.assert_not_called()

    assert metrics["num_skipped"] == 1
    assert metrics["num_inserted"] == 0
    assert metrics["num_updated"] == 0


@patch("core.ingest.process.resolve_org")
@patch("core.ingest.process.normalize_project_num")
@patch("core.ingest.process.insert_pis")
@patch("core.ingest.process.update_grant_embeddings")
@patch("core.ingest.process.update_research_grant")
@patch("core.ingest.process.insert_research_grant")
@patch("core.ingest.process.insert_organization")
@patch("core.ingest.process.fetch_existing_hash")
@patch("core.ingest.process.compute_content_hash")
def test_process_result_update(
    mock_compute_hash,
    mock_fetch_hash,
    mock_insert_org,
    mock_insert_grant,
    mock_update_grant,
    mock_update_embeddings,
    mock_insert_pis,
    mock_normalize,
    mock_resolve_org,
):
    """Test that process_result correctly updates a research grant when the existing hash does not match the computed hash."""

    mock_fetch_hash.return_value = (
        "R01CA123456",
        ("oldhash", 4),
    )
    mock_compute_hash.return_value = "newhash"
    mock_normalize.return_value = "R01CA123456"
    mock_resolve_org.return_value = ({"name": "Harvard"}, "payload")
    mock_insert_org.return_value = 7

    cur = Mock()

    result = {
        "project_num": "R01CA123456",
        "fiscal_year": 2025,
        "organization": {},
        "agency_ic_admin": {"abbreviation": "NCI"},
        "principal_investigators": [],
    }

    metrics = {
        "num_inserted": 0,
        "num_updated": 0,
        "num_skipped": 0,
    }

    process_result(
        result=result,
        cur=cur,
        org_cache={},
        ingest_id="run123",
        policy={},
        metrics=metrics,
    )

    mock_insert_grant.assert_not_called()

    mock_update_grant.assert_called_once()
    mock_update_embeddings.assert_called_once()
    mock_insert_pis.assert_called_once()

    assert metrics["num_updated"] == 1
    assert metrics["num_inserted"] == 0
    assert metrics["num_skipped"] == 0


@patch("core.ingest.process.resolve_org")
@patch("core.ingest.process.normalize_project_num")
@patch("core.ingest.process.insert_pis")
@patch("core.ingest.process.update_grant_embeddings")
@patch("core.ingest.process.update_research_grant")
@patch("core.ingest.process.insert_research_grant")
@patch("core.ingest.process.insert_organization")
@patch("core.ingest.process.fetch_existing_hash")
@patch("core.ingest.process.compute_content_hash")
def test_process_result_missing_org(
    mock_compute_hash,
    mock_fetch_hash,
    mock_insert_org,
    mock_insert_grant,
    mock_update_grant,
    mock_update_embeddings,
    mock_insert_pis,
    mock_normalize,
    mock_resolve_org,
):
    """Test that process_result raises a ValueError when the organization cannot be resolved."""

    mock_fetch_hash.return_value = (None, None)
    mock_compute_hash.return_value = "hash123"
    mock_normalize.return_value = "R01CA123456"
    mock_resolve_org.return_value = (None, "missing")

    cur = Mock()

    result = {
        "project_num": "R01CA123456",
        "fiscal_year": 2025,
        "organization": {},
        "agency_ic_admin": {"abbreviation": "NCI"},
        "principal_investigators": [],
    }

    metrics = {
        "num_inserted": 0,
        "num_updated": 0,
        "num_skipped": 0,
    }

    with pytest.raises(
        ValueError,
        match="Could not resolve organization",
    ):
        process_result(
            result=result,
            cur=cur,
            org_cache={},
            ingest_id="run123",
            policy={},
            metrics=metrics,
        )

    mock_insert_org.assert_not_called()
    mock_insert_grant.assert_not_called()
    mock_update_grant.assert_not_called()
    mock_insert_pis.assert_not_called()
