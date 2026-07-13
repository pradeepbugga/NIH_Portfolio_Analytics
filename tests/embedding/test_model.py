from unittest.mock import patch, Mock
import numpy as np
from core.embedding.model import load_model, embed_batch

@patch("core.embedding.model.SentenceTransformer")
def test_load_model(mock_sentence_transformer):

    model = load_model(
        "NeuML/pubmedbert-base-embeddings",
        "cpu",
    )

    mock_sentence_transformer.assert_called_once_with(
        "NeuML/pubmedbert-base-embeddings",
        device="cpu",
    )

    assert model == mock_sentence_transformer.return_value


def test_embed_batch():

    model = Mock()

    model.encode.return_value = np.array(
        [[1, 2, 3]],
        dtype=np.float64,
    )

    vectors = embed_batch(
        model,
        ["hello world"],
    )

    model.encode.assert_called_once_with(
        ["hello world"],
        normalize_embeddings=True,
        convert_to_numpy=True,
    )

    assert vectors.dtype == np.float32