
import pytest
from core.search.combine import combine_and_sort, combine_and_sort_semantic_filter


def make_doc(
    grant_id="id1",
    title="Title",
    abstract="Abstract",
    vector_similarity=0.8,
    fiscal_year=2025,
    amount=100000,
):
    return {
        "grant_id": grant_id,
        "title": title,
        "subproject_id": None,
        "core_project_num": "core",
        "fiscal_year": fiscal_year,
        "amount": amount,
        "abstract": abstract,
        "phr": "PHR",
        "agency_ic": "HG",
        "activity_code": "R01",

        "project_start_date": "2025-01-01",
        "project_end_date": "2028-12-31",
        "budget_start_date": "2025-01-01",
        "budget_end_date": "2025-12-31",

        "org_name": "Harvard",
        "org_city": "Boston",
        "org_state": "MA",
        "org_country": "USA",

        "pi_first_name": "John",
        "pi_middle_name": None,
        "pi_last_name": "Smith",

        "vector_similarity": vector_similarity,

        "mechanistic": 1,
        "therapeutic": 0,
        "diagnostic": 0,
        "clinical": 0,
        "research_tool": 0,
        "infrastructure": 0,
        "education": 0,
        "obs_ep": 0,

        "summary": "Summary",
    }


def test_combine_and_sort():

    """ Happy Path -> Tests that one document + one score leads to one result with the expected fields and values.
    Fields are copied correctly, score becomes a float, and vector similarity is preserved"""

    docs = [
        make_doc(
            grant_id="id1",
            title="Grant Title",
            vector_similarity=0.92,
        )
    ]

    scores = [0.75]

    results = combine_and_sort(
        docs,
        scores,
        rerank_score_threshold=-2.0,
    )

    assert len(results) == 1

    result = results[0]

    assert result["grant_id"] == "id1"

    assert result["title"] == "Grant Title"

    assert result["score"] == 0.75

    assert result["vector_similarity"] == 0.92

    assert result["agency_ic"] == "HG"

    assert result["activity_code"] == "R01"

    assert result["summary"] == "Summary"

def test_combine_and_sort_filters_low_scores():

    """ Tests that documents with scores below the rerank_score_threshold are filtered out and do not appear in the results. """

    docs = [
        make_doc(grant_id="id1"),
        make_doc(grant_id="id2"),
    ]

    scores = [
        -3.0,
        0.5,
    ]

    results = combine_and_sort(
        docs,
        scores,
        rerank_score_threshold=-2.0,
    )

    assert len(results) == 1

    assert results[0]["grant_id"] == "id2"

    assert results[0]["score"] == 0.5

def test_combine_and_sort_excludes_threshold_value():


    """ Tests that documents with scores equal to the rerank_score_threshold are filtered out and do not appear in the results. """

    docs = [
        make_doc(grant_id="id1"),
    ]

    scores = [-2.0]

    results = combine_and_sort(
        docs,
        scores,
        rerank_score_threshold=-2.0,
    )

    assert results == []

def test_combine_and_sort_orders_by_score():

    """ Tests that results are sorted in descending order by score. """

    docs = [
        make_doc(grant_id="id1"),
        make_doc(grant_id="id2"),
        make_doc(grant_id="id3"),
    ]

    scores = [
        0.25,
        0.90,
        0.50,
    ]

    results = combine_and_sort(
        docs,
        scores,
        rerank_score_threshold=-2.0,
    )

    assert len(results) == 3

    assert [r["grant_id"] for r in results] == [
        "id2",
        "id3",
        "id1",
    ]

    assert [r["score"] for r in results] == [
        0.90,
        0.50,
        0.25,
    ]

def test_combine_and_sort_default_vector_similarity():

    """ Tests that if a document is missing the vector_similarity field, it is set to 0.0 in the results rather than throwing an error. """

    doc = make_doc()

    del doc["vector_similarity"]

    results = combine_and_sort(
        [doc],
        [0.80],
        rerank_score_threshold=-2.0,
    )

    assert len(results) == 1

    assert results[0]["vector_similarity"] == 0.0

def test_combine_and_sort_requires_equal_lengths():

    """ Tests that an error is raised if the docs and scores lists have different lengths. """

    docs = [
        make_doc(),
    ]

    scores = []

    with pytest.raises(AssertionError):

        combine_and_sort(
            docs,
            scores,
            rerank_score_threshold=-2.0,
        )

def test_combine_and_sort_semantic_filter():

    """ Tests that combine_and_sort_semantic_filter correctly filters out documents 
    with non-positive scores and sorts the remaining documents by score in descending order. """

    docs = [
        make_doc(grant_id="id1"),
        make_doc(grant_id="id2"),
        make_doc(grant_id="id3"),
    ]

    scores = [
        -3.0,
        0.40,
        0.90,
    ]

    results = combine_and_sort_semantic_filter(
        docs,
        scores,
    )

    assert len(results) == 2

    assert [r["grant_id"] for r in results] == [
        "id3",
        "id2",
    ]

    assert [r["score"] for r in results] == [
        0.90,
        0.40,
    ]