from unittest.mock import patch, Mock
from core.ingest.reporter_client import (
    backoff,
    fetch_projects,
    build_payload,
    PAGE_LIMIT,
    AGENCIES,
)


def test_backoff():
    """Test that the backoff function returns a value between 8 and 9 seconds for a given retry count."""

    value = backoff(3)

    assert 8 <= value <= 9


@patch("core.ingest.reporter_client.requests.post")
def test_fetch_projects(mock_post):
    """Test that fetch_projects correctly calls the NIH Reporter API and returns the expected JSON response."""

    response = Mock()
    response.json.return_value = {"results": []}

    mock_post.return_value = response

    result = fetch_projects({"a": 1})

    assert result == {"results": []}

    mock_post.assert_called_once()
    response.raise_for_status.assert_called_once()


def test_build_payload_new_search():
    """Test that build_payload correctly constructs the payload for a new search with fiscal year and agency."""

    payload = build_payload(
        fiscal_year=2025,
        agency="CA",
        offset=500,
        search_id=None,
    )

    assert payload["criteria"]["fiscal_years"] == [2025]
    assert payload["criteria"]["project_num_split"]["ic_code"] == "CA"

    assert payload["offset"] == 500
    assert payload["limit"] == PAGE_LIMIT


def test_build_payload_existing_search():
    """Test that build_payload correctly constructs the payload for an existing search with a search_id."""

    payload = build_payload(
        fiscal_year=2025,
        agency="CA",
        offset=1000,
        search_id="abc123",
    )

    assert payload == {
        "search_id": "abc123",
        "offset": 1000,
        "limit": PAGE_LIMIT,
    }
