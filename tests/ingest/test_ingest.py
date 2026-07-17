
import pytest
from unittest.mock import Mock, patch
import requests
from core.ingest.ingest import ingest_year, DataQualityError

def make_response(
    total=1,
    search_id="abc",
    results=None,
):
    if results is None:
        results = [
            {
                "project_num": "R01CA123456",
            }
        ]

    return {
        "search_id": search_id,
        "meta": {
            "total": total,
        },
        "results": results,
    }


@patch("core.ingest.ingest.time.sleep")
@patch("core.ingest.ingest.tqdm")
@patch("core.ingest.ingest.process_result")
@patch("core.ingest.ingest.fetch_projects")
@patch("core.ingest.ingest.build_payload")
@patch("core.ingest.ingest.AGENCIES", ["AA"])
def test_ingest_year(
    mock_build_payload,
    mock_fetch_projects,
    mock_process_result,
    mock_tqdm,
    mock_sleep,
):

    """ Tests that ingest_year correctly executes the full pipeline and returns the expected results. """

    conn = Mock()
    cur = Mock()

    org_cache = {}

    metrics = {
        "num_errors": 0,
    }

    mock_fetch_projects.return_value = make_response()

    pbar = Mock()
    mock_tqdm.return_value = pbar

    ingest_year(
        2025,
        conn,
        cur,
        org_cache,
        "ingest1",
        {},
        metrics,
    )

    mock_build_payload.assert_called()

    mock_fetch_projects.assert_called_once()

    mock_process_result.assert_called_once()

    pbar.update.assert_called_once_with(1)

    pbar.close.assert_called_once()

@patch("core.ingest.ingest.backoff")
@patch("core.ingest.ingest.time.sleep")
@patch("core.ingest.ingest.tqdm")
@patch("core.ingest.ingest.process_result")
@patch("core.ingest.ingest.fetch_projects")
@patch("core.ingest.ingest.build_payload")
@patch("core.ingest.ingest.AGENCIES", ["AA"])
def test_ingest_year_retry_success(
    mock_build_payload,
    mock_fetch_projects,
    mock_process_result,
    mock_tqdm,
    mock_sleep,
    mock_backoff,
):

    """ Tests that ingest_year correctly retries fetching projects on failure and succeeds on a subsequent attempt. """

    conn = Mock()
    cur = Mock()

    mock_fetch_projects.side_effect = [
        requests.RequestException(),
        make_response(),
    ]

    pbar = Mock()
    mock_tqdm.return_value = pbar

    ingest_year(
        2025,
        conn,
        cur,
        {},
        "id",
        {},
        {"num_errors": 0},
    )

    assert mock_fetch_projects.call_count == 2

    mock_backoff.assert_called_once_with(0)

    mock_sleep.assert_called()

@patch("core.ingest.ingest.MAX_RETRIES", 2)
@patch("core.ingest.ingest.time.sleep")
@patch("core.ingest.ingest.backoff")
@patch("core.ingest.ingest.fetch_projects")
@patch("core.ingest.ingest.build_payload")
@patch("core.ingest.ingest.AGENCIES", ["AA"])
def test_ingest_year_retry_exhausted(
    mock_build_payload,
    mock_fetch_projects,
    mock_backoff,
    mock_sleep,
):

    """ Tests that ingest_year correctly retries fetching projects on failure and raises an error after exhausting all retries. """

    conn = Mock()
    cur = Mock()

    mock_fetch_projects.side_effect = requests.RequestException()

    with pytest.raises(RuntimeError):

        ingest_year(
            2025,
            conn,
            cur,
            {},
            "id",
            {},
            {"num_errors": 0},
        )

    assert mock_fetch_projects.call_count == 3

@patch("core.ingest.ingest.record_error")
@patch("core.ingest.ingest.time.sleep")
@patch("core.ingest.ingest.tqdm")
@patch("core.ingest.ingest.process_result")
@patch("core.ingest.ingest.fetch_projects")
@patch("core.ingest.ingest.build_payload")
@patch("core.ingest.ingest.AGENCIES", ["AA"])
def test_ingest_year_data_quality_error(
    mock_build_payload,
    mock_fetch_projects,
    mock_process_result,
    mock_tqdm,
    mock_sleep,
    mock_record_error,
):

    """Tests that ingest_year correctly handles a DataQualityError raised during result processing by recording the error and rolling back the transaction. """

    conn = Mock()
    cur = Mock()

    metrics = {
        "num_errors": 0,
    }

    mock_fetch_projects.return_value = make_response()

    mock_process_result.side_effect = DataQualityError(
        "bad record"
    )

    pbar = Mock()
    mock_tqdm.return_value = pbar

    ingest_year(
        2025,
        conn,
        cur,
        {},
        "id",
        {},
        metrics,
    )

    conn.rollback.assert_called_once()

    mock_record_error.assert_called_once()

    assert metrics["num_errors"] == 1

@patch("core.ingest.ingest.PAGE_LIMIT", 1)
@patch("core.ingest.ingest.time.sleep")
@patch("core.ingest.ingest.tqdm")
@patch("core.ingest.ingest.process_result")
@patch("core.ingest.ingest.fetch_projects")
@patch("core.ingest.ingest.build_payload")
@patch("core.ingest.ingest.AGENCIES", ["AA"])
def test_ingest_year_pagination(
    mock_build_payload,
    mock_fetch_projects,
    mock_process_result,
    mock_tqdm,
    mock_sleep,
):

    """ Tests that ingest_year correctly handles pagination by fetching multiple pages of results and processing them. """

    conn = Mock()
    cur = Mock()

    mock_fetch_projects.side_effect = [
        make_response(total=2),
        make_response(total=2),
    ]

    pbar = Mock()
    mock_tqdm.return_value = pbar

    ingest_year(
        2025,
        conn,
        cur,
        {},
        "id",
        {},
        {"num_errors": 0},
    )

    assert mock_fetch_projects.call_count == 2

    assert mock_process_result.call_count == 2

    assert pbar.update.call_count == 2