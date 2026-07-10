from pathlib import 
import json

def build_batch_task (grant_id, title, abstract, prompt, model, reasoning=None):
    """
    Build a batch task for the given grant_id, title, and abstract.
    """
    task = {
        "custom_id": grant_id,
        "method": "POST",
        "url": "/v1/responses",
        "body": {
            "model": model,            
            "reasoning": reasoning,
            "input":[{"role": "system", "content": prompt}, 
                {"role": "user", "content": f"Title: {title}\nAbstract: {abstract}"}],
            #"safety_identifier":  "  safety identifier for gpt as some grants will be flagged 
        }
    }
    return task


# following function generates a batch file for the given grant_ids and their corresponding titles and abstracts

def generate_batch_jsonl(cur, output_path, prompt, model, reasoning=None, fiscal_year = 2025):
    """
    Generate a batch JSONL file for the given grant_ids and their corresponding titles and abstracts.
    """
    total_fetch = 0
    total_written = 0

    cur.execute("SELECT grant_id, project_title, abstract FROM researchgrants WHERE fiscal_year = %s", (fiscal_year,))

    with open(output_path, "w") as f:

        while True:
            batch_size = 1000
            rows = cur.fetchmany(batch_size)

            if not rows:
                break
            
            for row in rows:
                grant_id, title, abstract = row

                total_fetch += 1

                if abstract is None:
                    continue
                
                if len(abstract.split()) < 10:
                    continue

                task = build_batch_task(grant_id, title, abstract, prompt, model, reasoning)

                total_written += 1
                f.write(json.dumps(task) + "\n")

    return 
        {"total_fetch": total_fetch,
         "total_written": total_written}



def split_jsonl(input_path, output_dir, limit=25_000):
    """
    Split a JSONL file into multiple smaller JSONL files.

    Parameters
    ----------
    input_path : str | Path
        Path to the input JSONL file.
    output_dir : str | Path
        Directory where split files will be written.
    limit : int, optional
        Maximum number of records per file. Defaults to the
        current OpenAI Batch API limit (25,000).

    Returns
    -------
    list[Path]
        Paths to the generated JSONL files.
    """

    input_path = Path(input_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    stem = input_path.stem

    output_paths = []

    part = 1
    line_count = 0

    output_path = output_dir / f"{stem}_part_{part}.jsonl"
    output_paths.append(output_path)
    out_file = output_path.open("w")

    with input_path.open("r") as in_file:

        for line in in_file:

            if line_count == limit:
                out_file.close()

                part += 1
                line_count = 0

                output_path = output_dir / f"{stem}_part_{part}.jsonl"
                output_paths.append(output_path)
                out_file = output_path.open("w")

            out_file.write(line)
            line_count += 1

    out_file.close()

    return output_paths
    
def combined_jsonl(input_paths, output_path):
    """
    Combine multiple JSONL files into a single JSONL file.

    Parameters
    ----------
    input_paths : list[str | Path]
        Paths to the input JSONL files.
    output_path : str | Path
        Path to the output JSONL file.

    Returns
    -------
    Path
        Path to the generated combined JSONL file.
    """

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w") as out_file:

        for input_path in input_paths:
            input_path = Path(input_path)

            with input_path.open("r") as in_file:
                for line in in_file:
                    out_file.write(line)

    seen_grant_ids = set()
    duplicates = 0
    total_records = 0
    unique_records = 0

    with output_path.open("w") as out_file:
        for input_path in input_paths:
            input_path = Path(input_path)

            with input_path.open("r") as in_file:
                for line in in_file:
                    try:
                        record = json.loads(line)
                    except json.JSONDecodeError as e:
                        print(
                            f"Skipping invalid JSON line in {input_path}: "
                            f"{line.strip()}. Error: {e}"
                        )
                        continue

                    total_records += 1

                    grant_id = record.get("grant_id")

                    if grant_id is None:
                        print(
                            f"Record missing grant_id in {input_path}. "
                            "Keeping record."
                        )
                        out_file.write(line)
                        unique_records += 1

                    elif grant_id not in seen_grant_ids:
                        out_file.write(line)
                        seen_grant_ids.add(grant_id)
                        unique_records += 1

                    else:
                        duplicates += 1
                        print(
                            f"Duplicate grant_id {grant_id} found. "
                            "Skipping duplicate record."
                        )

    print(
        f"Combined {total_records} records into "
        f"{unique_records} unique records "
        f"({duplicates} duplicates skipped) "
        f"in {output_path}."
    )

    return output_path