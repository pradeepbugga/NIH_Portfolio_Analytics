from unittest.mock import Mock

from core.embedding.selection import stream_grants_to_embed


def test_stream_grants_to_embed():
    """ "
    Create a mock db cursor and test that stream_grants_to_embed executes the expected SQL query to fetch grants for embedding.
    """

    cur = Mock()

    stream_grants_to_embed(cur)

    cur.execute.assert_called_once()

    args, kwargs = cur.execute.call_args

    sql = args[0]

    assert "ResearchGrants" in sql
    assert "GrantEmbeddings" in sql
    assert "content_hash" in sql

    assert len(args) == 1
    assert kwargs == {}
