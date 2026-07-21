from pathlib import Path
import argparse
import json

import logging

from core.logging_config import configure_logging

from dotenv import load_dotenv
from openai import OpenAI

from core.llm.parser import (
    parse_classification_results,
    parse_summary_results,
    write_jsonl,
)

logger = logging.getLogger(__name__)

PARSERS = {
    "classification": parse_classification_results,
    "summary": parse_summary_results,
}


def main():
    configure_logging()

    load_dotenv()

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--batch-dir",
        type=Path,
        required=True,
        help="Directory containing batch_manifest.json",
    )

    args = parser.parse_args()

    try:

        batch_dir = args.batch_dir

        logger.info("Processing batch results from %s", batch_dir)

        # -------------------------
        # DETERMINE PARSER
        # -------------------------

        parser_fn = None

        path_parts = {part.lower() for part in batch_dir.parts}

        task_name = None

        for task, fn in PARSERS.items():
            if task in path_parts:
                task_name = task
                parser_fn = fn
                break

        if parser_fn is None:
            raise ValueError(f"Could not determine parser from directory: {batch_dir}")

        logger.info("Using %s parser.", task_name)

        # -------------------------
        # LOAD MANIFEST
        # -------------------------

        manifest_path = batch_dir / "batch_manifest.json"

        with open(manifest_path, "r") as f:
            manifest = json.load(f)

        logger.info("Loaded manifest with %d batch jobs", len(manifest))

        client = OpenAI()

        # -------------------------
        # DOWNLOAD AND PARSE BATCH RESULTS
        # -------------------------

        for entry in manifest:

            logger.info("Checking batch %s", entry["batch_id"])

            batch = client.batches.retrieve(entry["batch_id"])

            logger.info(
                "%s status: %s",
                entry["file"],
                batch.status,
            )

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

                logger.info("Downloaded results for %s", entry["file"])

                # -------------------------
                # Parse output
                # -------------------------

                parsed = parser_fn(content)

                parsed_path = batch_dir / f"{stem}_parsed.jsonl"

                write_jsonl(parsed_path, parsed)

                logger.info("Parsed %d responses for %s", len(parsed), entry["file"])

                # -------------------------
                # Download error file
                # -------------------------

                if batch.error_file_id:

                    errors = client.files.content(batch.error_file_id)

                    error_path = batch_dir / f"{stem}_errors.jsonl"

                    with open(error_path, "wb") as f:
                        f.write(errors.content)

                    logger.warning("Downloaded error file for %s", entry["file"])

                print(f"Finished {entry['file']}")

            elif batch.status == "failed":
                logger.error("%s failed.", entry["file"])

            elif batch.status == "cancelled":
                logger.warning("%s was cancelled.", entry["file"])

            elif batch.status == "expired":
                logger.warning("%s expired.", entry["file"])

            else:
                logger.info("%s still %s", entry["file"], batch.status)

        logger.info("Batch retrieval complete")

    except Exception:
        logger.exception("Error during batch retrieval.")
        raise


if __name__ == "__main__":
    main()
