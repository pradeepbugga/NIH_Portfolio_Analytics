import numpy as np
import pytest

from unittest.mock import AsyncMock, Mock, patch

from core.search.hybrid import hybrid_search_range


@pytest.mark.anyio
@patch("core.search.hybrid.dedupe_by_core_project")
@patch("core.search.hybrid.combine_and_sort")
@patch("core.search.hybrid.load_grant_texts")
@patch("core.search.hybrid.retrieve_candidates_range")
@patch("core.search.hybrid.expand_query_for_fts")
@patch("core.search.hybrid.embed_query")
async def test_hybrid_search_range_happy_path(
    mock_embed_query,
    mock_expand_query,
    mock_retrieve_candidates,
    mock_load_grant_texts,
    mock_combine_and_sort,
    mock_dedupe,
):
    """Tests that hybrid_search_range correctly executes the full pipeline and returns the expected results."""

    cur = Mock()

    #
    # Query embedding
    #

    mock_embed_query.return_value = np.array(
        [0.1, 0.2, 0.3],
        dtype=np.float32,
    )

    #
    # Query expansion
    #

    mock_expand_query.return_value = (
        "multiple sclerosis",
        ["ms"],
    )

    #
    # Candidate retrieval
    #

    candidates = [
        ("id1", 0.91),
        ("id2", 0.82),
    ]

    mock_retrieve_candidates.return_value = candidates

    #
    # Document loading
    #

    docs = [
        {
            "grant_id": "id1",
            "title": "Title 1",
        },
        {
            "grant_id": "id2",
            "title": "Title 2",
        },
    ]

    mock_load_grant_texts.return_value = docs

    #
    # Modal reranker
    #

    rerank_fn = Mock()

    rerank_fn.remote = Mock()

    rerank_fn.remote.aio = AsyncMock(
        return_value=[
            0.8,
            0.6,
        ]
    )

    #
    # Combine
    #

    ranked = [
        {
            "grant_id": "id1",
            "score": 0.8,
        },
        {
            "grant_id": "id2",
            "score": 0.6,
        },
    ]

    mock_combine_and_sort.return_value = ranked

    #
    # Dedupe
    #

    mock_dedupe.return_value = ranked

    #
    # Run
    #

    result = await hybrid_search_range(
        query="multiple sclerosis",
        cur=cur,
        rerank_fn=rerank_fn,
    )

    #
    # Verify pipeline
    #

    mock_embed_query.assert_called_once_with("multiple sclerosis")

    mock_expand_query.assert_called_once()

    mock_retrieve_candidates.assert_called_once()

    rerank_fn.remote.aio.assert_awaited_once_with(
        "multiple sclerosis",
        [
            "id1",
            "id2",
        ],
    )

    mock_load_grant_texts.assert_called_once_with(
        cur,
        [
            "id1",
            "id2",
        ],
    )

    assert docs[0]["vector_similarity"] == 0.91
    assert docs[1]["vector_similarity"] == 0.82

    mock_combine_and_sort.assert_called_once()

    mock_dedupe.assert_called_once_with(
        ranked,
    )

    #
    # Returned result
    #

    assert result["query"] == "multiple sclerosis"

    assert result["projects"] == ranked

    assert result["records"] == ranked

    assert result["candidates"] == candidates


@pytest.mark.anyio
@patch("core.search.hybrid.dedupe_by_core_project")
@patch("core.search.hybrid.combine_and_sort")
@patch("core.search.hybrid.load_grant_texts")
@patch("core.search.hybrid.retrieve_candidates_range")
@patch("core.search.hybrid.expand_query_for_fts")
@patch("core.search.hybrid.embed_query")
async def test_hybrid_search_range_no_candidates(
    mock_embed_query,
    mock_expand_query,
    mock_retrieve_candidates,
    mock_load_grant_texts,
    mock_combine_and_sort,
    mock_dedupe,
):
    """Tests that hybrid_search_range correctly handles the case where no candidates are retrieved and returns the expected results."""

    cur = Mock()

    mock_embed_query.return_value = np.array(
        [0.1, 0.2, 0.3],
        dtype=np.float32,
    )

    mock_expand_query.return_value = (
        "multiple sclerosis",
        [],
    )

    #
    # No candidates found
    #

    mock_retrieve_candidates.return_value = []

    rerank_fn = Mock()
    rerank_fn.remote = Mock()
    rerank_fn.remote.aio = AsyncMock()

    result = await hybrid_search_range(
        query="multiple sclerosis",
        cur=cur,
        rerank_fn=rerank_fn,
    )

    #
    # Verify downstream pipeline never runs
    #

    rerank_fn.remote.aio.assert_not_called()

    mock_load_grant_texts.assert_not_called()

    mock_combine_and_sort.assert_not_called()

    mock_dedupe.assert_not_called()

    #
    # Returned result
    #

    assert result["query"] == "multiple sclerosis"

    assert result["projects"] == []

    assert result["records"] == []

    assert result["candidates"] == []


@pytest.mark.anyio
@patch("core.search.hybrid.load_grant_texts")
@patch("core.search.hybrid.retrieve_candidates_range")
@patch("core.search.hybrid.expand_query_for_fts")
@patch("core.search.hybrid.embed_query")
async def test_hybrid_search_range_score_mismatch(
    mock_embed_query,
    mock_expand_query,
    mock_retrieve_candidates,
    mock_load_grant_texts,
):

    cur = Mock()

    mock_embed_query.return_value = np.array(
        [0.1, 0.2, 0.3],
        dtype=np.float32,
    )

    mock_expand_query.return_value = (
        "multiple sclerosis",
        [],
    )

    mock_retrieve_candidates.return_value = [
        ("id1", 0.91),
        ("id2", 0.82),
    ]

    #
    # Modal only returns ONE score instead of two
    #

    rerank_fn = Mock()
    rerank_fn.remote = Mock()
    rerank_fn.remote.aio = AsyncMock(
        return_value=[
            0.75,
        ]
    )

    result = await hybrid_search_range(
        query="multiple sclerosis",
        cur=cur,
        rerank_fn=rerank_fn,
    )

    #
    # Should stop immediately after mismatch
    #

    mock_load_grant_texts.assert_not_called()

    assert result["query"] == "multiple sclerosis"

    assert result["projects"] == []

    assert result["records"] == []


@pytest.mark.anyio
@patch("core.search.hybrid.dedupe_by_core_project")
@patch("core.search.hybrid.combine_and_sort")
@patch("core.search.hybrid.load_grant_texts")
@patch("core.search.hybrid.retrieve_candidates_range")
@patch("core.search.hybrid.expand_query_for_fts")
@patch("core.search.hybrid.embed_query")
async def test_hybrid_search_range_no_docs(
    mock_embed_query,
    mock_expand_query,
    mock_retrieve_candidates,
    mock_load_grant_texts,
    mock_combine_and_sort,
    mock_dedupe,
):
    """Tests that hybrid_search_range correctly handles the case where no documents are loaded and returns the expected results."""

    cur = Mock()

    mock_embed_query.return_value = np.array(
        [0.1, 0.2, 0.3],
        dtype=np.float32,
    )

    mock_expand_query.return_value = (
        "multiple sclerosis",
        [],
    )

    mock_retrieve_candidates.return_value = [
        ("id1", 0.91),
        ("id2", 0.82),
    ]

    #
    # Metadata lookup fails
    #

    mock_load_grant_texts.return_value = []

    rerank_fn = Mock()
    rerank_fn.remote = Mock()
    rerank_fn.remote.aio = AsyncMock(
        return_value=[
            0.8,
            0.6,
        ]
    )

    result = await hybrid_search_range(
        query="multiple sclerosis",
        cur=cur,
        rerank_fn=rerank_fn,
    )

    #
    # Pipeline stops before combining
    #

    mock_combine_and_sort.assert_not_called()

    mock_dedupe.assert_not_called()

    #
    # Returned result
    #

    assert result["query"] == "multiple sclerosis"

    assert result["projects"] == []

    assert result["records"] == []


@pytest.mark.anyio
@patch("core.search.hybrid.dedupe_by_core_project")
@patch("core.search.hybrid.combine_and_sort")
@patch("core.search.hybrid.load_grant_texts")
@patch("core.search.hybrid.retrieve_candidates_range")
@patch("core.search.hybrid.expand_query_for_fts")
@patch("core.search.hybrid.embed_query")
async def test_hybrid_search_range_injects_vector_similarity(
    mock_embed_query,
    mock_expand_query,
    mock_retrieve_candidates,
    mock_load_grant_texts,
    mock_combine_and_sort,
    mock_dedupe,
):
    """Tests that hybrid_search_range correctly injects vector similarity scores into the document metadata for use in downstream filtering and ranking."""

    cur = Mock()

    mock_embed_query.return_value = np.array(
        [0.1, 0.2, 0.3],
        dtype=np.float32,
    )

    mock_expand_query.return_value = (
        "multiple sclerosis",
        [],
    )

    candidates = [
        ("id1", 0.91),
        ("id2", 0.82),
    ]

    mock_retrieve_candidates.return_value = candidates

    docs = [
        {
            "grant_id": "id1",
            "title": "Title 1",
        },
        {
            "grant_id": "id2",
            "title": "Title 2",
        },
    ]

    mock_load_grant_texts.return_value = docs

    rerank_fn = Mock()
    rerank_fn.remote = Mock()
    rerank_fn.remote.aio = AsyncMock(
        return_value=[
            0.8,
            0.6,
        ]
    )

    mock_combine_and_sort.return_value = docs
    mock_dedupe.return_value = docs

    await hybrid_search_range(
        query="multiple sclerosis",
        cur=cur,
        rerank_fn=rerank_fn,
    )

    #
    # Verify vector similarities were injected
    #

    assert docs[0]["vector_similarity"] == 0.91
    assert docs[1]["vector_similarity"] == 0.82

    #
    # Verify combine_and_sort received the updated docs
    #

    combine_docs = mock_combine_and_sort.call_args.args[0]

    assert combine_docs[0]["vector_similarity"] == 0.91
    assert combine_docs[1]["vector_similarity"] == 0.82
