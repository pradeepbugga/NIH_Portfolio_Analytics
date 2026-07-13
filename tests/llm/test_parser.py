import json

from core.llm.parser import (
    parse_classification_results,
    parse_summary_results,
    write_jsonl,
)

# -------------------------------------------------------------------------
# TESTS for parse_classification_results function
# -------------------------------------------------------------------------

def make_classification_response(grant_id, reasoning, answer):

    """ Helper function to create a mock classification response for testing the parse_classification_results function."""

    return (
        '{"custom_id":"%s","response":{"body":{"output":[{"type":"message","content":[{"text":"{\\"reasoning\\":\\"%s\\",\\"answer\\":\\"%s\\"}"}]}]}}}'
        % (grant_id, reasoning, answer)
    )


def test_parse_classification_results_single_record():

    """
    Test that single classification result is correctly parsed into a record with the expected grant_id, reasoning, and answer.
    """

    batch_results = make_classification_response(
    "id1",
    "Strong biological rationale",
    "YES",
)

    records = parse_classification_results(batch_results)

    assert records == [
        {
            "grant_id": "id1",
            "reasoning": "Strong biological rationale",
            "answer": "YES",
        }
    ]

def test_parse_classification_results_multiple_records():

    """ Test that multiple classification results are correctly parsed into a list of records with the expected grant_ids, reasoning, and answers.
    """

    batch_results = "\n".join([
        make_classification_response(
            "id1",
            "Reasoning 1",
            "YES",
        ),
        make_classification_response(
            "id2",
            "Reasoning 2",
            "NO",
        ),
    ])

    records = parse_classification_results(batch_results)

    assert records == [
        {
            "grant_id": "id1",
            "reasoning": "Reasoning 1",
            "answer": "YES",
        },
        {
            "grant_id": "id2",
            "reasoning": "Reasoning 2",
            "answer": "NO",
        },
    ]


def test_parse_classification_results_ignores_blank_lines():

    batch_results = "\n\n".join([
        make_classification_response(
            "id1",
            "Reasoning 1",
            "YES",
        ),
        make_classification_response(
            "id2",
            "Reasoning 2",
            "NO",
        ),
    ])

    records = parse_classification_results(batch_results)

    assert len(records) == 2

    assert records[0]["grant_id"] == "id1"

    assert records[1]["grant_id"] == "id2"

# -------------------------------------------------------------------------
# TESTS for parse_summary_results function
# -------------------------------------------------------------------------

def make_summary_response(grant_id, summary):

    return (
        '{"custom_id":"%s","response":{"body":{"output":[{"type":"message","content":[{"text":"%s"}]}]}}}'
        % (grant_id, summary)
    )

def test_parse_summary_results_single_record():

    """ Test that a single summary result is correctly parsed into a record with the expected grant_id and summary.
    """

    batch_results = make_summary_response(
        "id1",
        "This is a two sentence summary."
    )

    records = parse_summary_results(batch_results)

    assert records == [
        {
            "grant_id": "id1",
            "summary": "This is a two sentence summary.",
        }
    ]

def test_parse_summary_results_multiple_records():

    ''' Tests JSONL iteration and parsing of multiple summary results, ensuring each record is correctly parsed with the expected grant_id and summary.'''

    batch_results = "\n".join([
        make_summary_response(
            "id1",
            "Summary one.",
        ),
        make_summary_response(
            "id2",
            "Summary two.",
        ),
    ])

    records = parse_summary_results(batch_results)

    assert records == [
        {
            "grant_id": "id1",
            "summary": "Summary one.",
        },
        {
            "grant_id": "id2",
            "summary": "Summary two.",
        },
    ]

def test_parse_summary_results_ignores_blank_lines():

    """ Test that blank lines in the batch results are ignored and do not affect the parsing of valid summary records.
    """

    batch_results = "\n\n".join([
        make_summary_response(
            "id1",
            "Summary one.",
        ),
        make_summary_response(
            "id2",
            "Summary two.",
        ),
    ])

    records = parse_summary_results(batch_results)

    assert len(records) == 2

    assert records[0]["grant_id"] == "id1"
    assert records[0]["summary"] == "Summary one."

    assert records[1]["grant_id"] == "id2"
    assert records[1]["summary"] == "Summary two."

# -------------------------------------------------------------------------
# TESTS for write_jsonl function
# -------------------------------------------------------------------------
def test_write_jsonl(tmp_path):

    """ Tests that 1) file is created, 2) one JSON object is written per line, and 
    3) the content of each line matches the expected records after parsing back from JSON.
    """

    records = [
        {
            "grant_id": "id1",
            "answer": "YES",
            "reasoning": "Reasoning 1",
        },
        {
            "grant_id": "id2",
            "answer": "NO",
            "reasoning": "Reasoning 2",
        },
    ]

    output_path = tmp_path / "results.jsonl"

    write_jsonl(output_path, records)

    assert output_path.exists()

    lines = output_path.read_text().splitlines()

    assert len(lines) == 2

    assert json.loads(lines[0]) == records[0]

    assert json.loads(lines[1]) == records[1]