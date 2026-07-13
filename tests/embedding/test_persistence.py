from unittest.mock import Mock
import numpy as np

from core.embedding.persistence import upsert_embedding, count_grants_to_embed

def test_upsert_embedding():

    """
    Create a mock db cursor and test that upsert_embedding executes the expected SQL query to insert or update an embedding.
    """

    cur = Mock()

    cfg = Mock()
    cfg.model_name = "pubmedbert"
    cfg.text_recipe = "title_abstract"
    cfg.normalization = "l2"
    cfg.embedding_version = "v1"

    vector = np.array([1.0, 2.0, 3.0])

    upsert_embedding(
        cur,
        grant_id="1R01CA123456-01",
        content_hash="abc123",
        cfg=cfg,
        vector=vector,
    )

    cur.execute.assert_called_once()

    sql, params = cur.execute.call_args[0]

    assert "INSERT INTO GrantEmbeddings" in sql
    assert "ON CONFLICT" in sql

    assert params == (
        "1R01CA123456-01",
        "abc123",
        "pubmedbert",
        "title_abstract",
        "l2",
        "v1",
        [1.0, 2.0, 3.0],
    )

def test_count_grants_to_embed():

    """
    Create a mock db cursor and test that count_grants_to_embed executes the expected SQL query to count grants needing embedding.
    """

    cur = Mock()

    cur.fetchone.return_value = (42,)

    count = count_grants_to_embed(cur)

    cur.execute.assert_called_once()

    assert count == 42