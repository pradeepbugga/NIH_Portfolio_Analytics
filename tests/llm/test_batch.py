from core.llm.batch import (
    build_classification_batch_task,
    build_summary_batch_task,
    generate_batch_jsonl,
    split_jsonl,
    combine_jsonl,
)

from unittest.mock import Mock
import json
from pathlib import Path

# --------------------------------------------------------------------------
# TESTS build_classification_batch_task function
# --------------------------------------------------------------------------


def test_build_classification_batch_task_structure():
    """
    Test that build_classification_batch_task returns a dictionary with the expected structure and content based on the input parameters.
    """

    task = build_classification_batch_task(
        grant_id="1R01CA123456-01",
        title="My Title",
        abstract="My Abstract",
        prompt="You are a classifier.",
        model="gpt-5.4-mini",
        reasoning={"effort": "medium"},
    )

    assert task["custom_id"] == "1R01CA123456-01"

    assert task["method"] == "POST"

    assert task["url"] == "/v1/responses"


def test_build_classification_batch_task_body():
    """
    Test that the body of the task returned by build_classification_batch_task contains the expected model, reasoning, and input structure.
    """

    task = build_classification_batch_task(
        grant_id="1R01CA123456-01",
        title="Title",
        abstract="Abstract",
        prompt="Prompt",
        model="gpt-5.4-mini",
        reasoning={"effort": "medium"},
    )

    body = task["body"]

    assert body["model"] == "gpt-5.4-mini"

    assert body["reasoning"] == {"effort": "medium"}

    assert body["input"][0]["role"] == "system"

    assert body["input"][0]["content"] == "Prompt"

    assert body["input"][1]["role"] == "user"

    assert body["input"][1]["content"] == ("Title: Title\nAbstract: Abstract")


def test_build_classification_batch_task_schema():
    """
    Test the JSON schema to ensure it has the expected structure and constraints for the classification output.
    """

    task = build_classification_batch_task(
        "id",
        "Title",
        "Abstract",
        "Prompt",
        "gpt-5.4-mini",
    )

    schema = task["body"]["text"]["format"]["schema"]

    assert schema["type"] == "object"

    assert schema["required"] == [
        "reasoning",
        "answer",
    ]

    assert schema["additionalProperties"] is False

    assert schema["properties"]["answer"]["enum"] == [
        "YES",
        "NO",
    ]


def test_build_classification_batch_task_without_reasoning():
    """
    Test that build_classification_batch_task can be called without providing reasoning and that the resulting task has a body with "reasoning" set to None.
    """

    task = build_classification_batch_task(
        grant_id="id",
        title="Title",
        abstract="Abstract",
        prompt="Prompt",
        model="gpt-5.4-mini",
    )

    assert task["body"]["reasoning"] is None


# --------------------------------------------------------------------------
# TESTS build_summary_batch_task function
# --------------------------------------------------------------------------


def test_build_summary_batch_task_structure():

    task = build_summary_batch_task(
        grant_id="1R01CA123456-01",
        title="My Title",
        abstract="My Abstract",
        prompt="Summarize this grant.",
        model="gpt-5.4-mini",
        reasoning={"effort": "medium"},
    )

    assert task["custom_id"] == "1R01CA123456-01"

    assert task["method"] == "POST"

    assert task["url"] == "/v1/responses"


def test_build_summary_batch_task_body():

    task = build_summary_batch_task(
        grant_id="id",
        title="Title",
        abstract="Abstract",
        prompt="Prompt",
        model="gpt-5.4-mini",
        reasoning={"effort": "medium"},
    )

    body = task["body"]

    assert body["model"] == "gpt-5.4-mini"

    assert body["reasoning"] == {"effort": "medium"}

    assert body["input"][0]["content"] == "Prompt"

    assert body["input"][1]["content"] == ("Title: Title\nAbstract: Abstract")


def test_build_summary_batch_task_has_no_json_schema():

    task = build_summary_batch_task(
        "id",
        "Title",
        "Abstract",
        "Prompt",
        "gpt-5.4-mini",
    )

    body = task["body"]

    assert "text" not in body


def test_build_summary_batch_task_without_reasoning():

    task = build_summary_batch_task(
        grant_id="id",
        title="Title",
        abstract="Abstract",
        prompt="Prompt",
        model="gpt-5.4-mini",
    )

    assert task["body"]["reasoning"] is None


# --------------------------------------------------------------------------
# Tests generate_batch_jsonl function
# --------------------------------------------------------------------------


def test_generate_batch_jsonl(tmp_path):
    """
    Happy path - Test that generate_batch_jsonl correctly fetches grant data from the database cursor,
    applies the length filter, builds tasks using the provided build_task function,
    and writes the expected number of tasks to the output JSONL file.
    """
    cur = Mock()

    cur.fetchmany.side_effect = [
        [
            (
                "id1",
                "Title1",
                "This abstract contains well over ten words so it will be written.",
            ),
            (
                "id2",
                "Title2",
                "This abstract also contains enough words to pass the length filter.",
            ),
        ],
        [],
    ]

    build_task = Mock(
        side_effect=lambda gid, title, abstract, prompt, model, reasoning: {
            "grant_id": gid
        }
    )

    output_file = tmp_path / "batch.jsonl"

    stats = generate_batch_jsonl(
        cur=cur,
        output_path=output_file,
        prompt="Prompt",
        build_task=build_task,
        model="gpt-5.4-mini",
    )

    cur.execute.assert_called_once()

    assert build_task.call_count == 2

    assert stats["total_fetch"] == 2
    assert stats["total_written"] == 2

    lines = output_file.read_text().splitlines()

    assert len(lines) == 2

    assert json.loads(lines[0])["grant_id"] == "id1"


def test_generate_batch_jsonl_skips_missing_abstract(tmp_path):

    cur = Mock()

    cur.fetchmany.side_effect = [
        [
            (
                "id1",
                "Title1",
                None,
            )
        ],
        [],
    ]

    build_task = Mock()

    output_file = tmp_path / "batch.jsonl"

    stats = generate_batch_jsonl(
        cur=cur,
        output_path=output_file,
        prompt="Prompt",
        build_task=build_task,
        model="gpt-5.4-mini",
    )

    cur.execute.assert_called_once()

    build_task.assert_not_called()

    assert stats["total_fetch"] == 1
    assert stats["total_written"] == 0

    assert output_file.read_text() == ""


def test_generate_batch_jsonl_skips_short_abstract(tmp_path):

    cur = Mock()

    cur.fetchmany.side_effect = [
        [
            (
                "id1",
                "Title1",
                "Too short.",
            )
        ],
        [],
    ]

    build_task = Mock()

    output_file = tmp_path / "batch.jsonl"

    stats = generate_batch_jsonl(
        cur=cur,
        output_path=output_file,
        prompt="Prompt",
        build_task=build_task,
        model="gpt-5.4-mini",
    )

    cur.execute.assert_called_once()

    build_task.assert_not_called()

    assert stats["total_fetch"] == 1
    assert stats["total_written"] == 0

    assert output_file.read_text() == ""


# ---------------------------------------------------------------------------
# Tests split_jsonl function
# ---------------------------------------------------------------------------


def test_split_jsonl(tmp_path):

    input_file = tmp_path / "input.jsonl"

    # Create a JSONL file with 5 records
    with input_file.open("w") as f:
        for i in range(5):
            f.write(json.dumps({"grant_id": f"id{i}"}) + "\n")

    output_dir = tmp_path / "split"

    output_paths = split_jsonl(
        input_path=input_file,
        output_dir=output_dir,
        limit=2,
    )

    # Three files should be created
    assert len(output_paths) == 3

    # Count the lines in each file
    counts = []

    for path in output_paths:
        assert path.exists()
        with path.open() as f:
            counts.append(len(f.readlines()))

    assert counts == [2, 2, 1]


# ----------------------------------------------------------------------------
# Tests combine_jsonl.py
# ----------------------------------------------------------------------------


def test_combine_jsonl_removes_duplicates(tmp_path):

    file1 = tmp_path / "part1.jsonl"
    file2 = tmp_path / "part2.jsonl"

    with file1.open("w") as f:
        f.write(json.dumps({"grant_id": "id1", "answer": "YES"}) + "\n")
        f.write(json.dumps({"grant_id": "id2", "answer": "NO"}) + "\n")

    with file2.open("w") as f:
        f.write(json.dumps({"grant_id": "id2", "answer": "NO"}) + "\n")
        f.write(json.dumps({"grant_id": "id3", "answer": "YES"}) + "\n")

    output = tmp_path / "combined.jsonl"

    returned_path = combine_jsonl(
        [file1, file2],
        output,
    )

    assert returned_path == output

    with output.open() as f:
        records = [json.loads(line) for line in f]

    assert len(records) == 3

    assert [r["grant_id"] for r in records] == [
        "id1",
        "id2",
        "id3",
    ]
