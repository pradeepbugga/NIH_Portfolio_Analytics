import pandas as pd

from unittest.mock import MagicMock, patch

from core.search.fill_abstract import add_abstracts


@patch("core.search.fill_abstract.get_db_connection")
def test_add_abstracts(mock_get_db_connection):

    """ Happy path - test that add_abstracts correctly fetches abstracts for the given grant IDs and adds them to the DataFrame. """

    df = pd.DataFrame({
        "grant_id": [
            "id1",
            "id2",
        ]
    })

    conn = MagicMock()
    cur = MagicMock()

    mock_get_db_connection.return_value = conn
    conn.cursor.return_value.__enter__.return_value = cur

    cur.fetchall.return_value = [
        ("id1", "Abstract 1"),
        ("id2", "Abstract 2"),
    ]

    result = add_abstracts(df)

    assert result["abstract"].tolist() == [
        "Abstract 1",
        "Abstract 2",
    ]

    conn.close.assert_called_once()

@patch("core.search.fill_abstract.get_db_connection")
def test_add_abstracts_missing_grant(mock_get_db_connection):

    """ Tests that add_abstracts handles missing abstracts gracefully by leaving NaN values
     in the abstract column for grant IDs that are not found in the database. """ 

    df = pd.DataFrame({
        "grant_id": [
            "id1",
            "id2",
        ]
    })

    conn = MagicMock()
    cur = MagicMock()

    mock_get_db_connection.return_value = conn
    conn.cursor.return_value.__enter__.return_value = cur

    cur.fetchall.return_value = [
        ("id1", "Abstract 1"),
    ]

    result = add_abstracts(df)

    assert result.loc[0, "abstract"] == "Abstract 1"
    assert pd.isna(result.loc[1, "abstract"])

    conn.close.assert_called_once()


@patch("core.search.fill_abstract.get_db_connection")
def test_add_abstracts_queries_expected_ids(mock_get_db_connection):

    """ Tests correct SQL parameters - that add_abstracts queries the database with the expected list of unique grant IDs from the DataFrame. """

    df = pd.DataFrame({
        "grant_id": [
            "id1",
            "id2",
        ]
    })

    conn = MagicMock()
    cur = MagicMock()

    mock_get_db_connection.return_value = conn
    conn.cursor.return_value.__enter__.return_value = cur

    cur.fetchall.return_value = []

    add_abstracts(df)

    cur.execute.assert_called_once()

    sql = cur.execute.call_args[0][0]
    params = cur.execute.call_args[0][1]

    assert "ResearchGrants" in sql

    assert params == (
        ["id1", "id2"],
    )

    conn.close.assert_called_once()

@patch("core.search.fill_abstract.get_db_connection")
def test_add_abstracts_uses_unique_grant_ids(mock_get_db_connection):

    """ Tests duplicate grant IDs - that add_abstracts correctly extracts the unique grant IDs 
    from the DataFrame and queries the database with the deduplicated list. """

    df = pd.DataFrame({
        "grant_id": [
            "id1",
            "id1",
            "id2",
        ]
    })

    conn = MagicMock()
    cur = MagicMock()

    mock_get_db_connection.return_value = conn
    conn.cursor.return_value.__enter__.return_value = cur

    cur.fetchall.return_value = [
        ("id1", "Abstract 1"),
        ("id2", "Abstract 2"),
    ]

    add_abstracts(df)

    params = cur.execute.call_args[0][1]

    assert params == (
        ["id1", "id2"],
    )

    conn.close.assert_called_once()

@patch("core.search.fill_abstract.get_db_connection")
def test_add_abstracts_closes_connection_on_exception(mock_get_db_connection):

    """ Testing resource cleanup - that add_abstracts properly closes the database connection even if an exception occurs during query execution. """

    df = pd.DataFrame({
        "grant_id": ["id1"]
    })

    conn = MagicMock()
    cur = MagicMock()

    mock_get_db_connection.return_value = conn
    conn.cursor.return_value.__enter__.return_value = cur

    cur.execute.side_effect = RuntimeError("boom")

    import pytest

    with pytest.raises(RuntimeError):
        add_abstracts(df)

    conn.close.assert_called_once()