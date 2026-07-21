from unittest.mock import Mock
import numpy as np

from core.search.candidate_retrieval import (
    retrieve_candidates_topk,
    retrieve_candidates_range,
    retrieve_candidates_range_portfolio,
)

# ----------------------------------------------------------------
# TESTS for retrieve_candidates_topk function
# ----------------------------------------------------------------


def test_retrieve_candidates_topk():
    """Verify that retrieve_candidates_topk executes the expected SQL query and returns the correct results."""

    cur = Mock()

    cur.fetchall.return_value = [
        ("id1", 0.95),
        ("id2", 0.91),
    ]

    results = retrieve_candidates_topk(
        cur,
        np.array([1.0, 2.0, 3.0]),
        top_k=100,
    )

    cur.execute.assert_called_once()

    sql = cur.execute.call_args[0][0]

    params = cur.execute.call_args[0][1]

    assert "GrantEmbeddings" in sql

    assert "LIMIT %s" in sql

    assert params[2] == 100

    assert results == [
        ("id1", 0.95),
        ("id2", 0.91),
    ]


# ----------------------------------------------------------------
# TESTS for retrieve_candidates_range function
# ----------------------------------------------------------------


def test_retrieve_candidates_range_semantic():
    """Verifies early return of retrieve_candidates_range when search_mode is 'semantic' and that the expected SQL query is executed."""

    cur = Mock()

    semantic_results = [
        ("id1", 0.94),
        ("id2", 0.87),
    ]

    cur.fetchall.return_value = semantic_results

    results = retrieve_candidates_range(
        cur=cur,
        query_vec_list=[1.0, 2.0, 3.0],
        similarity_threshold=0.25,
        search_mode="semantic",
    )

    cur.execute.assert_called_once()

    sql = cur.execute.call_args[0][0]

    assert "GrantEmbeddings" in sql

    assert "ORDER BY d" in sql

    assert results == semantic_results


def test_retrieve_candidates_range_semantic_with_fiscal_year():
    """Verifies that retrieve_candidates_range correctly incorporates fiscal year filtering into the SQL query when search_mode is 'semantic'."""

    cur = Mock()

    cur.fetchall.return_value = [
        ("id1", 0.95),
    ]

    retrieve_candidates_range(
        cur=cur,
        query_vec_list=[1.0, 2.0],
        similarity_threshold=0.25,
        fiscal_years=[2025],
    )

    sql = cur.execute.call_args[0][0]

    params = cur.execute.call_args[0][1]

    assert "JOIN ResearchGrants" in sql

    assert "ANY(%s)" in sql

    assert params[1] == [2025]


def test_retrieve_candidates_range_hybrid_merge():
    """Verifies that retrieve_candidates_range correctly merges semantic and keyword search results when search_mode is 'hybrid'."""

    cur = Mock()

    cur.fetchall.side_effect = [
        # semantic search
        [
            ("id1", 0.95),
            ("id2", 0.90),
        ],
        # keyword search
        [
            ("id2",),
            ("id3",),
        ],
    ]

    results = retrieve_candidates_range(
        cur=cur,
        query_vec_list=[1.0],
        similarity_threshold=0.25,
        search_mode="hybrid",
        query_text="multiple sclerosis",
        synonyms=[],
    )

    assert cur.execute.call_count == 2

    assert sorted(results) == sorted(
        [
            ("id1", 0.95),
            ("id2", 0.90),
            ("id3", 0.0),
        ]
    )


# ----------------------------------------------------------------
# TESTS for retrieve_candidates_range_portfolio function
# ----------------------------------------------------------------


def test_retrieve_candidates_range_portfolio_constrained():
    """Tests ontology-constrained candidate retrieval meaning that only grants with IDs in the allowed_grant_ids list are returned,
    and that the expected SQL query is executed."""

    cur = Mock()

    cur.fetchall.return_value = [
        ("id1", 0.94),
        ("id2", 0.87),
    ]

    results = retrieve_candidates_range_portfolio(
        cur=cur,
        query_vec_list=[1.0, 2.0, 3.0],
        similarity_threshold=0.25,
        allowed_grant_ids=[
            "id1",
            "id2",
        ],
    )

    cur.execute.assert_called_once()

    sql = cur.execute.call_args[0][0]

    params = cur.execute.call_args[0][1]

    assert "grant_id = ANY(%s)" in sql

    assert params[1] == [
        "id1",
        "id2",
    ]

    assert results == [
        ("id1", 0.94),
        ("id2", 0.87),
    ]


def test_retrieve_candidates_range_portfolio_global():
    """Tests global candidate retrieval meaning that grants are retrieved from the entire portfolio without filtering by allowed_grant_ids,
    and that the expected SQL query is executed."""

    cur = Mock()

    cur.fetchall.return_value = [
        ("id1", 0.95),
    ]

    results = retrieve_candidates_range_portfolio(
        cur=cur,
        query_vec_list=[1.0, 2.0],
        similarity_threshold=0.25,
        allowed_grant_ids=None,
    )

    cur.execute.assert_called_once()

    sql = cur.execute.call_args[0][0]

    assert "grant_id = ANY(%s)" not in sql

    assert "GrantEmbeddings" in sql

    assert results == [
        ("id1", 0.95),
    ]
