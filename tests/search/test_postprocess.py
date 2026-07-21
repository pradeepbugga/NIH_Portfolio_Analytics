from core.search.postprocess import dedupe_by_core_project


def test_dedupe_by_core_project_no_duplicates():
    """Tests that dedupe_by_core_project returns the original list when there are no duplicate core_project_num values."""

    results = [
        {"grant_id": "id1", "core_project_num": "1R01CA111111"},
        {"grant_id": "id2", "core_project_num": "1R01CA222222"},
    ]

    deduped = dedupe_by_core_project(results)

    assert deduped == results


def test_dedupe_by_core_project_removes_duplicates():
    """Tests that dedupe_by_core_project removes duplicate records based on core_project_num, keeping only the first occurrence."""

    results = [
        {
            "grant_id": "id1",
            "core_project_num": "1R01CA111111",
        },
        {
            "grant_id": "id2",
            "core_project_num": "1R01CA111111",
        },
        {
            "grant_id": "id3",
            "core_project_num": "1R01CA222222",
        },
    ]

    deduped = dedupe_by_core_project(results)

    assert len(deduped) == 2


def test_dedupe_by_core_project_empty():
    """Tests that dedupe_by_core_project returns an empty list when given an empty list."""

    assert dedupe_by_core_project([]) == []
