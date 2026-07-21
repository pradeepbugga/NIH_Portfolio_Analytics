from unittest.mock import Mock, patch
import numpy as np

from core.embedding.embedding_job import run_embedding_job
from core.embedding.config import EmbeddingConfig
import pytest


@patch("core.embedding.embedding_job.tqdm")
@patch("core.embedding.embedding_job.upsert_embedding")
@patch("core.embedding.embedding_job.embed_batch")
@patch("core.embedding.embedding_job.count_grants_to_embed")
@patch("core.embedding.embedding_job.load_model")
@patch("core.embedding.embedding_job.stream_grants_to_embed")
@patch("core.embedding.embedding_job.get_db_connection")
def test_run_embedding_job_no_grants(
    mock_get_db_connection,
    mock_stream,
    mock_load_model,
    mock_count,
    mock_embed_batch,
    mock_upsert,
    mock_tqdm,
):
    """First we will test the case where there are no grants to embed,
    and verify that the embedding job runs without errors and does not attempt to embed anything.
    """

    # Fake database connections
    read_conn = Mock()
    write_conn = Mock()

    mock_get_db_connection.side_effect = [
        read_conn,
        write_conn,
    ]

    # Fake cursors
    read_cur = Mock()
    read_cur.__iter__ = Mock(return_value=iter([]))

    write_cur = Mock()
    count_cur = Mock()

    read_conn.cursor.return_value = read_cur
    write_conn.cursor.side_effect = [
        write_cur,
        count_cur,
    ]

    # Progress bar
    mock_tqdm.return_value = Mock()

    # Database says there are zero grants
    mock_count.return_value = 0

    cfg = EmbeddingConfig()

    run_embedding_job(cfg)

    mock_stream.assert_called_once_with(read_cur)
    mock_load_model.assert_called_once_with(
        cfg.model_name,
        cfg.device,
    )

    mock_embed_batch.assert_not_called()
    mock_upsert.assert_not_called()

    write_conn.commit.assert_not_called()


@patch("core.embedding.embedding_job.tqdm")
@patch("core.embedding.embedding_job.upsert_embedding")
@patch("core.embedding.embedding_job.embed_batch")
@patch("core.embedding.embedding_job.count_grants_to_embed")
@patch("core.embedding.embedding_job.load_model")
@patch("core.embedding.embedding_job.stream_grants_to_embed")
@patch("core.embedding.embedding_job.get_db_connection")
def test_run_embedding_job_partial_batch(
    mock_get_db_connection,
    mock_stream,
    mock_load_model,
    mock_count,
    mock_embed_batch,
    mock_upsert,
    mock_tqdm,
):
    """Next we will test the case where there are some grants to embed, but the total number is not a multiple of the batch size.
    This will verify that the embedding job correctly handles trailing batches."""

    read_conn = Mock()
    write_conn = Mock()

    mock_get_db_connection.side_effect = [
        read_conn,
        write_conn,
    ]

    read_cur = Mock()

    # One grant only
    read_cur.__iter__ = Mock(
        return_value=iter(
            [
                (
                    "1R01CA123456-01",
                    "Title",
                    "Abstract",
                    "hash123",
                )
            ]
        )
    )

    write_cur = Mock()
    count_cur = Mock()

    read_conn.cursor.return_value = read_cur

    write_conn.cursor.side_effect = [
        write_cur,
        count_cur,
    ]

    mock_tqdm.return_value = Mock()

    mock_count.return_value = 1

    mock_model = Mock()
    mock_load_model.return_value = mock_model

    mock_embed_batch.return_value = np.array(
        [[1.0, 2.0, 3.0]],
        dtype=np.float32,
    )

    cfg = EmbeddingConfig(
        batch_size=10,
        device="cpu",
    )

    run_embedding_job(cfg)

    mock_embed_batch.assert_called_once_with(
        mock_model,
        ["Title Abstract"],
    )

    mock_upsert.assert_called_once()

    write_conn.commit.assert_called_once()

    mock_tqdm.return_value.update.assert_called_once_with(1)


@patch("core.embedding.embedding_job.tqdm")
@patch("core.embedding.embedding_job.upsert_embedding")
@patch("core.embedding.embedding_job.embed_batch")
@patch("core.embedding.embedding_job.count_grants_to_embed")
@patch("core.embedding.embedding_job.load_model")
@patch("core.embedding.embedding_job.stream_grants_to_embed")
@patch("core.embedding.embedding_job.get_db_connection")
def test_run_embedding_job_full_batch(
    mock_get_db_connection,
    mock_stream,
    mock_load_model,
    mock_count,
    mock_embed_batch,
    mock_upsert,
    mock_tqdm,
):
    """Next we will test the case where there are exactly as many grants to embed as the batch size."""

    read_conn = Mock()
    write_conn = Mock()

    mock_get_db_connection.side_effect = [
        read_conn,
        write_conn,
    ]

    read_cur = Mock()

    # Two grants
    read_cur.__iter__ = Mock(
        return_value=iter(
            [
                (
                    "1R01CA123456-01",
                    "Title",
                    "Abstract",
                    "hash123",
                ),
                (
                    "1R01CA123457-01",
                    "Title2",
                    "Abstract2",
                    "hash124",
                ),
            ]
        )
    )

    write_cur = Mock()
    count_cur = Mock()

    read_conn.cursor.return_value = read_cur

    write_conn.cursor.side_effect = [
        write_cur,
        count_cur,
    ]

    mock_tqdm.return_value = Mock()

    mock_count.return_value = 2

    mock_model = Mock()
    mock_load_model.return_value = mock_model

    mock_embed_batch.return_value = np.array(
        [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]],
        dtype=np.float32,
    )

    cfg = EmbeddingConfig(
        batch_size=2,
        device="cpu",
    )

    run_embedding_job(cfg)

    mock_stream.assert_called_once_with(read_cur)

    mock_load_model.assert_called_once_with(
        cfg.model_name,
        cfg.device,
    )

    mock_embed_batch.assert_called_once_with(
        mock_model,
        ["Title Abstract", "Title2 Abstract2"],
    )

    assert mock_upsert.call_count == 2

    write_conn.commit.assert_called_once()

    mock_tqdm.return_value.update.assert_called_once_with(2)

    calls = mock_upsert.call_args_list

    assert calls[0].args[1] == "1R01CA123456-01"
    assert calls[0].args[2] == "hash123"
    assert calls[1].args[1] == "1R01CA123457-01"
    assert calls[1].args[2] == "hash124"


@patch("core.embedding.embedding_job.tqdm")
@patch("core.embedding.embedding_job.upsert_embedding")
@patch("core.embedding.embedding_job.embed_batch")
@patch("core.embedding.embedding_job.count_grants_to_embed")
@patch("core.embedding.embedding_job.load_model")
@patch("core.embedding.embedding_job.stream_grants_to_embed")
@patch("core.embedding.embedding_job.get_db_connection")
def test_run_embedding_job_multiple_batches(
    mock_get_db_connection,
    mock_stream,
    mock_load_model,
    mock_count,
    mock_embed_batch,
    mock_upsert,
    mock_tqdm,
):
    """Next we will test the case where there are two batches worth of grants to embed,
    and verify that the embedding job correctly processes both batches and commits after each batch.
    """

    read_conn = Mock()
    write_conn = Mock()

    mock_get_db_connection.side_effect = [
        read_conn,
        write_conn,
    ]

    read_cur = Mock()

    # Two grants
    read_cur.__iter__ = Mock(
        return_value=iter(
            [
                (
                    "1R01CA123456-01",
                    "Title",
                    "Abstract",
                    "hash123",
                ),
                (
                    "1R01CA123457-01",
                    "Title2",
                    "Abstract2",
                    "hash124",
                ),
                (
                    "1R01CA123458-01",
                    "Title3",
                    "Abstract3",
                    "hash125",
                ),
                (
                    "1R01CA123459-01",
                    "Title4",
                    "Abstract4",
                    "hash126",
                ),
            ]
        )
    )

    write_cur = Mock()
    count_cur = Mock()

    read_conn.cursor.return_value = read_cur

    write_conn.cursor.side_effect = [
        write_cur,
        count_cur,
    ]

    mock_tqdm.return_value = Mock()

    mock_count.return_value = 4

    mock_model = Mock()
    mock_load_model.return_value = mock_model

    mock_embed_batch.return_value = np.array(
        [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]],
        dtype=np.float32,
    )

    cfg = EmbeddingConfig(
        batch_size=2,
        device="cpu",
    )

    run_embedding_job(cfg)

    assert mock_embed_batch.call_count == 2

    assert mock_upsert.call_count == 4

    assert write_conn.commit.call_count == 2

    assert mock_tqdm.return_value.update.call_count == 2

    mock_tqdm.return_value.update.assert_any_call(2)

    calls = mock_embed_batch.call_args_list

    assert calls[0].args[1] == ["Title Abstract", "Title2 Abstract2"]

    assert calls[1].args[1] == ["Title3 Abstract3", "Title4 Abstract4"]


@patch("core.embedding.embedding_job.tqdm")
@patch("core.embedding.embedding_job.upsert_embedding")
@patch("core.embedding.embedding_job.embed_batch")
@patch("core.embedding.embedding_job.count_grants_to_embed")
@patch("core.embedding.embedding_job.load_model")
@patch("core.embedding.embedding_job.stream_grants_to_embed")
@patch("core.embedding.embedding_job.get_db_connection")
def test_run_embedding_job_closes_resources_on_exception(
    mock_get_db_connection,
    mock_stream,
    mock_load_model,
    mock_count,
    mock_embed_batch,
    mock_upsert,
    mock_tqdm,
):
    """Finally we will test that if an exception occurs during the embedding job, all database connections and cursors are properly closed."""

    read_conn = Mock()
    write_conn = Mock()

    mock_get_db_connection.side_effect = [
        read_conn,
        write_conn,
    ]

    read_cur = Mock()
    read_cur.__iter__ = Mock(
        return_value=iter(
            [
                (
                    "id1",
                    "Title",
                    "Abstract",
                    "hash1",
                )
            ]
        )
    )

    write_cur = Mock()
    count_cur = Mock()

    read_conn.cursor.return_value = read_cur

    write_conn.cursor.side_effect = [
        write_cur,
        count_cur,
    ]

    mock_tqdm.return_value = Mock()

    mock_count.return_value = 1

    mock_load_model.return_value = Mock()

    mock_embed_batch.side_effect = RuntimeError("boom")

    cfg = EmbeddingConfig(
        batch_size=10,
        device="cpu",
    )

    with pytest.raises(RuntimeError):
        run_embedding_job(cfg)

    read_cur.close.assert_called_once()
    write_cur.close.assert_called_once()
    count_cur.close.assert_called_once()

    read_conn.close.assert_called_once()
    write_conn.close.assert_called_once()

    mock_tqdm.return_value.close.assert_called_once()
