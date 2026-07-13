def parse_classification_results(batch_results: str) -> list[dict]:
    """
    Parse successful OpenAI Batch API classification results.

    Parameters
    ----------
    batch_results 
        Raw contents of the Batch API output JSONL file.

    Returns
    -------
    list[dict]
        Parsed classification records.
    """

    parsed_records = []

    results = (
        json.loads(line)
        for line in batch_results.splitlines()
        if line.strip()
    )

    for result in results:

        grant_id = result["custom_id"]

        output = result["response"]["body"]["output"]

        message = next(
            item for item in output
            if item["type"] == "message"
        )

        answer = json.loads(
            message["content"][0]["text"]
        )

        parsed_records.append({
            "grant_id": grant_id,
            "reasoning": answer["reasoning"],
            "answer": answer["answer"],
        })

    return parsed_records


def parse_summary_results(batch_results: str) -> list[dict]:
    """
    Parse successful OpenAI Batch API summary results.

    Parameters
    ----------
    batch_results
        Raw contents of the Batch API output JSONL file.

    Returns
    -------
    list[dict]
        Parsed summarization records.
    """

    parsed_records = []

    results = (
        json.loads(line)
        for line in batch_results.splitlines()
        if line.strip()
    )

    for result in results:

        grant_id = result["custom_id"]

        output = result["response"]["body"]["output"]

        message = next(
            item for item in output
            if item["type"] == "message"
        )

        parsed_records.append({
            "grant_id": grant_id,
            "summary": message["content"][0]["text"].strip(),
        })

    return parsed_records


def write_jsonl(path: str | Path, records: list[dict]):
    """
    Write a list of dictionaries to a JSONL file.
    """

    with open(path, "w") as f:
        for record in records:
            f.write(json.dumps(record) + "\n")