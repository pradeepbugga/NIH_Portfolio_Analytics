from unittest.mock import Mock

from core.search.load_docs import load_grant_texts


def make_row(
    grant_id="4R00AA029754-03",
    title="Pathological AMPA receptor adaptations governing dependence-escalated alcohol self-administration",
    abstract="Project Summary ...",
):
    return (
        grant_id,
        title,
        None,  # subproject_id
        abstract,
        "R00AA029754",  # core_project_num
        2025,
        249000,
        "PROJECT NARRATIVE",
        "NIAAA",
        "R00",
        "2025-08-21",
        "2028-07-31",
        "2025-08-21",
        "2026-07-31",
        "Loyola University Chicago",
        "Maywood",
        "IL",
        "United States",
        "Julien",
        None,
        "Hoffman",
        1,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        "This study tests whether...",
    )


def test_load_grant_texts_empty():
    """Tests empty input to load_grant_texts and verifies that it returns an empty list without executing any SQL queries."""

    cur = Mock()

    docs = load_grant_texts(cur, [])

    assert docs == []

    cur.execute.assert_not_called()


def test_load_grant_texts():
    """Tests happy path of load_grant_texts with a single grant_id and verifies that it
    executes the expected SQL query and returns the correct document structure."""

    cur = Mock()

    cur.fetchall.return_value = [
        make_row(
            grant_id="id1",
            title="Grant Title",
            abstract="Grant abstract.",
        )
    ]

    docs = load_grant_texts(
        cur,
        ["id1"],
    )

    cur.execute.assert_called_once()

    assert len(docs) == 1

    doc = docs[0]

    assert doc["grant_id"] == "id1"

    assert doc["title"] == "Grant Title"

    assert doc["abstract"] == "Grant abstract."

    assert doc["agency_ic"] == "NIAAA"

    assert doc["activity_code"] == "R00"

    assert doc["org_name"] == "Loyola University Chicago"

    assert doc["summary"] == "This study tests whether..."

    assert doc["text"] == "Grant Title Grant abstract."


def test_load_grant_texts_preserves_order():
    """Tests that load_grant_texts preserves the order of grant_ids in the output documents, and that the expected SQL query is executed."""

    cur = Mock()

    cur.fetchall.return_value = [
        make_row(
            grant_id="id2",
            title="Title 2",
            abstract="Abstract 2",
        ),
        make_row(
            grant_id="id1",
            title="Title 1",
            abstract="Abstract 1",
        ),
    ]

    docs = load_grant_texts(
        cur,
        [
            "id1",
            "id2",
        ],
    )

    cur.execute.assert_called_once()

    assert docs[0]["grant_id"] == "id1"
    assert docs[1]["grant_id"] == "id2"


def test_load_grant_texts_skips_missing_grants():
    """Tests if missing grant is skipped in load_grant_texts and that the expected SQL query is executed."""

    cur = Mock()

    cur.fetchall.return_value = [
        make_row(
            grant_id="id1",
        )
    ]

    docs = load_grant_texts(
        cur,
        [
            "id1",
            "id2",
        ],
    )

    cur.execute.assert_called_once()

    assert len(docs) == 1
    assert docs[0]["grant_id"] == "id1"


def test_load_grant_texts_handles_null_title_and_abstract():
    """Tests that load_grant_texts correctly handles null title and abstract by replacing them with empty strings,
    and that the expected SQL query is executed."""
    cur = Mock()

    cur.fetchall.return_value = [
        make_row(
            grant_id="id1",
            title=None,
            abstract=None,
        )
    ]
    docs = load_grant_texts(
        cur,
        ["id1"],
    )

    cur.execute.assert_called_once()

    assert docs[0]["title"] is None
    assert docs[0]["abstract"] is None

    assert docs[0]["text"] == " "
