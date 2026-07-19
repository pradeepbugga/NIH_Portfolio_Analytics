from pathlib import Path
import argparse
import json

from dotenv import load_dotenv
from openai import OpenAI

from core.llm.parser import (
    parse_classification_results,
    parse_summary_results,
    write_jsonl,
)

PARSERS = {
    "classification": parse_classification_results,
    "summary": parse_summary_results,
}


def main():

    load_dotenv()

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--batch-dir",
        type=Path,
        required=True,
        help="Directory containing batch_manifest.json",
    )

    args = parser.parse_args()

    batch_dir = args.batch_dir

    # -------------------------
    # DETERMINE PARSER
    # -------------------------

    parser_fn = None

    path_parts = {part.lower() for part in batch_dir.parts}

    for task, fn in PARSERS.items():
        if task in path_parts:
            parser_fn = fn
            break

    if parser_fn is None:
        raise ValueError(f"Could not determine parser from directory: {batch_dir}")

    # -------------------------
    # LOAD MANIFEST
    # -------------------------

    manifest_path = batch_dir / "batch_manifest.json"

    with open(manifest_path, "r") as f:
        manifest = json.load(f)

    client = OpenAI()

    # -------------------------
    # DOWNLOAD AND PARSE BATCH RESULTS
    # -------------------------

    for entry in manifest:

        batch = client.batches.retrieve(entry["batch_id"])

        print(f"{entry['file']}: {batch.status}")

        if batch.status == "completed":

            # -------------------------
            # Download successful output
            # -------------------------

            output = client.files.content(batch.output_file_id)

            content = output.content.decode("utf-8")

            stem = Path(entry["file"]).stem

            raw_path = batch_dir / f"{stem}_raw.jsonl"

            with open(raw_path, "w") as f:
                f.write(content)

            # -------------------------
            # Parse output
            # -------------------------

            parsed = parser_fn(content)

            parsed_path = batch_dir / f"{stem}_parsed.jsonl"

            write_jsonl(parsed_path, parsed)

            # -------------------------
            # Download error file
            # -------------------------

            if batch.error_file_id:

                errors = client.files.content(batch.error_file_id)

                error_path = batch_dir / f"{stem}_errors.jsonl"

                with open(error_path, "wb") as f:
                    f.write(errors.content)

            print(f"Finished {entry['file']}")

        elif batch.status == "failed":
            print(f"{entry['file']} failed.")

        elif batch.status == "cancelled":
            print(f"{entry['file']} was cancelled.")

        elif batch.status == "expired":
            print(f"{entry['file']} expired.")

        else:
            print(f"{entry['file']} still {batch.status}")

    print("Done.")


if __name__ == "__main__":
    main()
