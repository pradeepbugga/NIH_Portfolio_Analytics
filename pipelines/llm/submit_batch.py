from openai import OpenAI
from pathlib import Path
import argparse
import json

import logging

from core.logging_config import configure_logging

from dotenv import load_dotenv

logger = logging.getLogger(__name__)


def main():
    configure_logging()

    load_dotenv()

    client = OpenAI()

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--batch-dir",
        type=Path,
        required=True,
        help="Directory containing JSONL batch files.",
    )

    args = parser.parse_args()

    try:

        batch_dir = args.batch_dir

        logger.info("Submitting batch files from %s", batch_dir)

        manifest = []

        json_files = sorted(batch_dir.glob("*.jsonl"))

        logger.info("Found %d JSONL files to submit.", len(json_files))

        for jsonl_path in json_files:

            logger.info("Submitting %s", jsonl_path.name)

            with open(jsonl_path, "rb") as f:
                batch_file = client.files.create(
                    file=f,
                    purpose="batch",
                )

            batch = client.batches.create(
                input_file_id=batch_file.id,
                endpoint="/v1/responses",
                completion_window="24h",
                metadata={
                    "description": jsonl_path.stem,
                },
            )

            manifest.append(
                {
                    "jsonl_path": str(jsonl_path),
                    "file_id": batch_file.id,
                    "batch_id": batch.id,
                }
            )

            logger.info(
                "Submitted batch for %s: file_id=%s, batch_id=%s",
                jsonl_path.name,
                batch_file.id,
                batch.id,
            )

        # Write manifest to JSON file
        manifest_path = batch_dir / "batch_manifest.json"
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=4)

        logger.info("Batch submission manifest written to %s", manifest_path)

    except Exception:
        logger.exception("Error during batch submission.")
        raise


if __name__ == "__main__":
    main()
