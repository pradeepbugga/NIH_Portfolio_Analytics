from pathlib import Path
import argparse
import logging
from core.logging_config import configure_logging

from core.llm.batch import combine_jsonl

logger = logging.getLogger(__name__)


def main():
    configure_logging()

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--batch-dir",
        type=Path,
        required=True,
        help="Directory containing parsed batch results.",
    )

    args = parser.parse_args()

    try:

        batch_dir = args.batch_dir

        logger.info("Combining parsed results from %s", batch_dir)

        # Parsed outputs from successful batches
        input_paths = sorted(batch_dir.glob("*_parsed.jsonl"))

        # Include manually recovered error/flagged records if present
        input_paths.extend(sorted(batch_dir.glob("*_recovered.jsonl")))

        if not input_paths:
            raise ValueError(f"No parsed JSONL files found in {batch_dir}")

        output_path = batch_dir / "combined_results.jsonl"

        combine_jsonl(
            input_paths=input_paths,
            output_path=output_path,
        )

        logger.info("Combined %d files into %s", len(input_paths), output_path)

    except Exception:
        logger.exception("Error during combining parsed results.")
        raise


if __name__ == "__main__":
    main()
