import numpy as np

from unittest.mock import Mock, patch, ANY
from core.search.query_embedding import (
    get_query_encoder,
    embed_query,
    warmup_query_encoder,
)


@patch("core.search.query_embedding.SentenceTransformer")
def test_get_query_encoder_caches_model(mock_sentence_transformer):

    import core.search.query_embedding as qe

    qe.get_query_encoder.cache_clear()

    model = Mock()
    mock_sentence_transformer.return_value = model

    first = qe.get_query_encoder()
    second = qe.get_query_encoder()

    assert first is second

    mock_sentence_transformer.assert_called_once()

    mock_sentence_transformer.assert_called_once_with(
        "NeuML/pubmedbert-base-embeddings",
        device=ANY,
    )


@patch("core.search.query_embedding.get_query_encoder")
def test_embed_query(mock_get_encoder):

    model = Mock()

    model.encode.return_value = np.array([[1.0, 2.0, 3.0]])

    mock_get_encoder.return_value = model

    vector = embed_query("multiple sclerosis")

    model.encode.assert_called_once_with(
        ["multiple sclerosis"],
        convert_to_numpy=True,
        normalize_embeddings=True,
    )

    assert np.array_equal(vector, np.array([1.0, 2.0, 3.0]))


@patch("core.search.query_embedding.get_query_encoder")
def test_warmup_query_encoder(mock_get_encoder):

    model = Mock()

    mock_get_encoder.return_value = model

    warmup_query_encoder()

    model.encode.assert_called_once_with(
        ["warmup text for gpu initialization"],
        normalize_embeddings=True,
        show_progress_bar=False,
    )


@patch("core.search.query_embedding.SentenceTransformer")
def test_get_query_encoder_cache_clear(mock_sentence_transformer):

    get_query_encoder.cache_clear()

    mock_sentence_transformer.return_value = Mock()

    get_query_encoder()
    get_query_encoder.cache_clear()
    get_query_encoder()

    assert mock_sentence_transformer.call_count == 2
