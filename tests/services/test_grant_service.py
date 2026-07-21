from unittest.mock import Mock, patch
import pytest

from core.services.grant_service import fetch_grant_abstract


@pytest.mark.anyio
@patch("core.services.grant_service.get_db_connection")
async def test_fetch_grant_abstract_success(mock_get_db_connection):
    """Test that fetch_grant_abstract successfully retrieves the abstract for a given grant ID."""

    conn = Mock()
    cur = Mock()

    mock_get_db_connection.return_value = conn
    conn.cursor.return_value = cur
    cur.fetchone.return_value = ("This is an abstract.",)

    result = await fetch_grant_abstract("1R01CA123456-01")

    assert result == {"abstract": "This is an abstract."}

    cur.execute.assert_called_once_with(
        """
                SELECT abstract
                FROM ResearchGrants
                WHERE grant_id = %s
                """,
        ("1R01CA123456-01",),
    )

    cur.close.assert_called_once()
    conn.close.assert_called_once()


@pytest.mark.asyncio
@patch("core.services.grant_service.get_db_connection")
async def test_fetch_grant_abstract_missing_text(mock_get_db_connection):
    """Test that fetch_grant_abstract returns a default message when the abstract is missing or null."""

    conn = Mock()
    cur = Mock()

    mock_get_db_connection.return_value = conn
    conn.cursor.return_value = cur
    cur.fetchone.return_value = (None,)

    result = await fetch_grant_abstract("1R01CA123456-01")

    assert result == {"abstract": "No abstract available for this record."}

    cur.close.assert_called_once()
    conn.close.assert_called_once()


@pytest.mark.asyncio
@patch("core.services.grant_service.get_db_connection")
async def test_fetch_grant_abstract_not_found(mock_get_db_connection):
    """Test that fetch_grant_abstract raises a ValueError when the grant ID is not found in the database."""

    conn = Mock()
    cur = Mock()

    mock_get_db_connection.return_value = conn
    conn.cursor.return_value = cur
    cur.fetchone.return_value = None

    with pytest.raises(
        ValueError,
        match="Grant not found.",
    ):
        await fetch_grant_abstract("1R01CA123456-01")

    cur.execute.assert_called_once()
    cur.close.assert_called_once()
    conn.close.assert_called_once()
