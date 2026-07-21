from core.utils.query_expansion import expand_query_for_fts


def test_expand_query_single_match():
    """Tests that expand_query_for_fts correctly expands a query with a single matching synonym."""

    registry = {"multiple sclerosis": ["ms", "eae"]}

    query, synonyms = expand_query_for_fts(
        "multiple sclerosis",
        registry,
    )

    assert query == "multiple sclerosis"
    assert synonyms == ["ms", "eae"]


def test_expand_query_no_match():
    """Tests that expand_query_for_fts returns an empty list of synonyms when there are no matches."""

    registry = {"multiple sclerosis": ["ms", "eae"]}

    query, synonyms = expand_query_for_fts(
        "heart disease",
        registry,
    )

    assert query == "heart disease"
    assert synonyms == []


def test_expand_query_multiple_matches():
    """Tests that expand_query_for_fts correctly expands a query with multiple matching synonyms."""

    registry = {
        "heart disease": ["hf"],
        "disease": ["illness"],
    }

    query, synonyms = expand_query_for_fts(
        "heart disease",
        registry,
    )

    assert query == "heart disease"
    assert synonyms == ["hf", "illness"]
