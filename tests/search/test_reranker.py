import numpy as np

from unittest.mock import ANY, Mock, patch

from core.search.reranker import (
    get_reranker,
    rerank,
    rerank_batch,
    warmup_reranker,
)


@patch("core.search.reranker.CrossEncoder")
def test_get_reranker_caches_model(mock_cross_encoder):
    """Tests cache behavior of get_reranker by calling it twice and asserting that the model is only loaded once."""

    get_reranker.cache_clear()

    model = Mock()

    mock_cross_encoder.return_value = model

    first = get_reranker()
    second = get_reranker()

    assert first is second

    mock_cross_encoder.assert_called_once_with(
        "./models/rerankers/v4",
        device=ANY,
    )


@patch("core.search.reranker.get_reranker")
def test_rerank(mock_get_reranker):
    """Tests that rerank correctly calls the model's predict method with the expected inputs and returns the expected scores."""

    model = Mock()

    model.predict.return_value = np.array(
        [
            0.8,
            0.2,
        ]
    )

    mock_get_reranker.return_value = model

    scores = rerank(
        "multiple sclerosis",
        [
            "doc1",
            "doc2",
        ],
    )

    model.predict.assert_called_once_with(
        [
            ("multiple sclerosis", "doc1"),
            ("multiple sclerosis", "doc2"),
        ]
    )

    assert np.array_equal(
        scores,
        np.array(
            [
                0.8,
                0.2,
            ]
        ),
    )


@patch("core.search.reranker.get_reranker")
def test_rerank_batch_single_batch(mock_get_reranker):
    """Tests that rerank_batch correctly processes a batch of documents smaller than the batch size and returns the expected scores."""

    model = Mock()

    model.predict.return_value = [
        0.8,
        0.3,
    ]

    mock_get_reranker.return_value = model

    scores = rerank_batch(
        "query",
        [
            "doc1",
            "doc2",
        ],
        batch_size=4,
    )

    model.predict.assert_called_once_with(
        [
            ("query", "doc1"),
            ("query", "doc2"),
        ]
    )

    assert scores == [
        0.8,
        0.3,
    ]


@patch("core.search.reranker.get_reranker")
def test_rerank_batch_multiple_batches(mock_get_reranker):
    """Tests that rerank_batch correctly processes multiple batches of documents and returns the expected scores in the correct order."""

    model = Mock()

    model.predict.side_effect = [
        [
            0.1,
            0.2,
        ],
        [
            0.3,
            0.4,
        ],
        [
            0.5,
        ],
    ]

    mock_get_reranker.return_value = model

    scores = rerank_batch(
        "query",
        [
            "d1",
            "d2",
            "d3",
            "d4",
            "d5",
        ],
        batch_size=2,
    )

    assert model.predict.call_count == 3

    assert scores == [
        0.1,
        0.2,
        0.3,
        0.4,
        0.5,
    ]


@patch("core.search.reranker.get_reranker")
def test_rerank_batch_empty(mock_get_reranker):
    """Tests that rerank_batch returns an empty list when given an empty list of documents and does not call the model's predict method."""

    model = Mock()

    mock_get_reranker.return_value = model

    scores = rerank_batch(
        "query",
        [],
    )

    assert scores == []

    model.predict.assert_not_called()


@patch("core.search.reranker.get_reranker")
def test_warmup_reranker(mock_get_reranker):
    """Tests that warmup_reranker calls the model's predict method with the expected inputs to warm up the model."""

    model = Mock()

    mock_get_reranker.return_value = model

    warmup_reranker()

    model.predict.assert_called_once()

    inputs = model.predict.call_args[0][0]

    kwargs = model.predict.call_args.kwargs

    assert len(inputs) == 2048

    assert inputs[0] == (
        "warmup",
        "warmup",
    )

    assert kwargs["batch_size"] == 32

    assert kwargs["show_progress_bar"] is False


@patch("core.search.reranker.CrossEncoder")
def test_get_reranker_cache_clear(mock_cross_encoder):
    """Tests that clearing the cache of get_reranker forces the model to be loaded again on the next call."""

    get_reranker.cache_clear()

    mock_cross_encoder.return_value = Mock()

    get_reranker()

    get_reranker.cache_clear()

    get_reranker()

    assert mock_cross_encoder.call_count == 2
