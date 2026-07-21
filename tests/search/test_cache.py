import pytest
from unittest.mock import Mock
from datetime import date, datetime
from core.search.cache import (
    json_serial,
    get_cached_results,
    save_cached_results,
)


def test_json_serial_datetime():

    dt = datetime(2025, 7, 1, 12, 30, 0)

    assert json_serial(dt) == "2025-07-01T12:30:00"


def test_json_serial_date():

    d = date(2025, 7, 1)

    assert json_serial(d) == "2025-07-01"


def test_json_serial_invalid_type():

    with pytest.raises(TypeError):
        json_serial(123)


def test_get_cached_results_hit():

    cur = Mock()

    expected = '{"projects": []}'

    cur.fetchone.return_value = (expected,)

    results = get_cached_results(
        cur,
        "multiple sclerosis",
    )

    cur.execute.assert_called_once_with(
        "SELECT results FROM cached_searches WHERE query = %s",
        ("multiple sclerosis",),
    )

    assert results == expected


def test_get_cached_results_miss():

    cur = Mock()

    cur.fetchone.return_value = None

    results = get_cached_results(
        cur,
        "multiple sclerosis",
    )

    assert results is None


def test_save_cached_results():

    cur = Mock()

    results = {
        "model_version": "v2",
        "projects": [
            {"grant_id": "id1"},
            {"grant_id": "id2"},
        ],
    }

    save_cached_results(
        cur,
        "multiple sclerosis",
        results,
    )

    cur.execute.assert_called_once()

    sql = cur.execute.call_args[0][0]

    params = cur.execute.call_args[0][1]

    assert "cached_searches" in sql

    assert params[0] == "multiple sclerosis"

    assert params[1] == "v2"

    assert params[3] == 2
