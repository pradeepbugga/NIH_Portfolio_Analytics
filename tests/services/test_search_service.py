from unittest.mock import Mock, patch
import pytest

from core.services.search_service import normalize_query, search


def test_normalize_query():
    """Test that the normalize_query function correctly normalizes input strings by removing extra whitespace and converting to lowercase."""

    assert normalize_query("  Multiple   Sclerosis   ") == "multiple sclerosis"


@pytest.mark.anyio
@patch("core.services.search_service.save_debug_json")
@patch("core.services.search_service.format_output_grants")
@patch("core.services.search_service.extract_ontology_distribution")
@patch("core.services.search_service.extract_funding")
@patch("core.services.search_service.hybrid_search_range")
@patch("core.services.search_service.save_cached_results")
@patch("core.services.search_service.get_cached_results")
@patch("core.services.search_service.get_db_connection")
async def test_search_cache_hit(
    mock_get_db,
    mock_get_cached,
    mock_save_cached,
    mock_hybrid,
    mock_extract_funding,
    mock_extract_ontology,
    mock_format,
    mock_save_debug,
):
    """Test the search function when there is a cache hit. It should return cached results without calling the hybrid search or saving to cache."""

    conn = Mock()
    cur = Mock()

    mock_get_db.return_value = conn
    conn.cursor.return_value = cur

    cached = {"records": [{"grant_id": "1"}]}

    mock_get_cached.return_value = cached
    mock_extract_funding.return_value = ([2025], [100])
    mock_extract_ontology.return_value = (["Tool"], [1])
    mock_format.return_value = [{"grant_id": "1"}]

    mock_rerank = Mock()

    result = await search(
        query="Multiple Sclerosis",
        rerank_fn=mock_rerank,
        synonym_registry={},
    )

    mock_hybrid.assert_not_called()
    mock_save_cached.assert_not_called()
    conn.commit.assert_not_called()

    assert result["query"] == "multiple sclerosis"
    assert result["results"] == [{"grant_id": "1"}]

    cur.close.assert_called_once()
    conn.close.assert_called_once()


@pytest.mark.anyio
@patch("core.services.search_service.save_debug_json")
@patch("core.services.search_service.format_output_grants")
@patch("core.services.search_service.extract_ontology_distribution")
@patch("core.services.search_service.extract_funding")
@patch("core.services.search_service.hybrid_search_range")
@patch("core.services.search_service.save_cached_results")
@patch("core.services.search_service.get_cached_results")
@patch("core.services.search_service.get_db_connection")
async def test_search_cache_miss(
    mock_get_db,
    mock_get_cached,
    mock_save_cached,
    mock_hybrid,
    mock_extract_funding,
    mock_extract_ontology,
    mock_format,
    mock_save_debug,
):
    """Test the search function when there is a cache miss. It should call the hybrid search, save results to cache, and return the new results."""

    conn = Mock()
    cur = Mock()

    mock_get_db.return_value = conn
    conn.cursor.return_value = cur

    mock_get_cached.return_value = None

    search_results = {"records": [{"grant_id": "1"}]}

    mock_hybrid.return_value = search_results

    mock_extract_funding.return_value = ([2025], [100])
    mock_extract_ontology.return_value = (["Tool"], [1])
    mock_format.return_value = [{"grant_id": "1"}]

    mock_rerank = Mock()

    result = await search(
        query="Multiple Sclerosis",
        rerank_fn=mock_rerank,
        synonym_registry={},
    )

    mock_hybrid.assert_called_once()
    mock_save_cached.assert_called_once()
    conn.commit.assert_called_once()

    assert result["query"] == "multiple sclerosis"

    cur.close.assert_called_once()
    conn.close.assert_called_once()


@pytest.mark.anyio
@patch("core.services.search_service.format_output_grants")
@patch("core.services.search_service.extract_ontology_distribution")
@patch("core.services.search_service.extract_funding")
@patch("core.services.search_service.get_cached_results")
@patch("core.services.search_service.get_db_connection")
async def test_search_cleanup_on_exception(
    mock_get_db,
    mock_get_cached,
    mock_extract_funding,
    mock_extract_ontology,
    mock_format,
):
    """Test that the search function properly closes the database cursor and connection even if an exception occurs during processing."""

    conn = Mock()
    cur = Mock()

    mock_get_db.return_value = conn
    conn.cursor.return_value = cur

    mock_get_cached.return_value = {"records": []}

    mock_extract_funding.return_value = ([], [])
    mock_extract_ontology.return_value = ([], [])

    mock_format.side_effect = RuntimeError("boom")

    mock_rerank = Mock()

    with pytest.raises(RuntimeError):
        await search(
            "test",
            rerank_fn=mock_rerank,
            synonym_registry={},
        )

    cur.close.assert_called_once()
    conn.close.assert_called_once()
