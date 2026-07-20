import pytest
from unittest.mock import Mock, AsyncMock, patch

from core.services.portfolio_service import (
    SearchRequest,
    get_grants_by_category,
    _determine_candidate_ids,
    _rerank_and_format,
)

# -----------------------------
# TESTS the get_grants_by_category function
# -----------------------------


@pytest.mark.anyio
async def test_get_grants_by_category_invalid_category():
    """Test the get_grants_by_category function with an invalid category. It should raise a ValueError."""

    with pytest.raises(ValueError):
        await get_grants_by_category(
            year=2025,
            category="fake_category",
        )


def test_determine_candidate_ids_existing_ids():
    """Test the _determine_candidate_ids function when existing_ids are provided. It should return the existing_ids without querying the database."""

    payload = SearchRequest(
        year=2025,
        category="mechanistic",
        query="cancer",
        existing_ids=["1", "2", "3"],
        query_history_count=1,
    )

    cur = Mock()

    ids = _determine_candidate_ids(
        payload,
        cur,
        column="mechanistic",
    )

    assert ids == ["1", "2", "3"]

    cur.execute.assert_not_called()


# -----------------------------
# TESTS the _rerank_and_format function
# -----------------------------


def test_determine_candidate_ids_category_sql():
    """Test the _determine_candidate_ids function when no existing_ids are provided. It should query the database and return the candidate IDs."""

    payload = SearchRequest(
        year=2025,
        category="mechanistic",
        query="cancer",
        existing_ids=[],
        query_history_count=1,
    )

    cur = Mock()

    cur.fetchall.return_value = [
        ("A",),
        ("B",),
    ]

    ids = _determine_candidate_ids(
        payload,
        cur,
        column="mechanistic",
    )

    assert ids == ["A", "B"]

    cur.execute.assert_called_once()


@pytest.mark.anyio
async def test_rerank_and_format():
    """Test rerank orchestration and formatting of results. It should call the rerank function, combine results, and format the output."""

    docs = [
        {
            "grant_id": "1",
            "text": "doc one",
        },
        {
            "grant_id": "2",
            "text": "doc two",
        },
    ]

    rerank_fn = Mock()
    rerank_fn.remote.aio = AsyncMock(return_value=[0.9, 0.1])

    ranked = [
        {"grant_id": "1"},
        {"grant_id": "2"},
    ]

    formatted = [
        {"grant_id": "1"},
        {"grant_id": "2"},
    ]

    with (
        patch(
            "core.services.portfolio_service.combine_and_sort_semantic_filter",
            return_value=ranked,
        ) as combine_mock,
        patch(
            "core.services.portfolio_service.format_output_grants",
            return_value=formatted,
        ) as format_mock,
    ):

        result = await _rerank_and_format(
            "cancer",
            docs,
            rerank_fn,
        )

    rerank_fn.remote.aio.assert_awaited_once_with(
        "cancer",
        ["doc one", "doc two"],
    )

    combine_mock.assert_called_once()

    format_mock.assert_called_once_with(ranked)

    assert result == formatted


@pytest.mark.anyio
async def test_rerank_and_format_empty_docs():
    """Test the _rerank_and_format function when the docs list is empty. It should return an empty list and not call the rerank function."""
    rerank_fn = Mock()

    result = await _rerank_and_format(
        "cancer",
        [],
        rerank_fn,
    )

    assert result == []

    assert not rerank_fn.remote.aio.called
