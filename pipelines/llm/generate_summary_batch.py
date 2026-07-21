import argparse
from pathlib import Path

import logging

from dotenv import load_dotenv

from core.db.connection import get_db_connection
from core.llm.prompt_loader import load_prompt
from core.llm.batch import build_summary_batch_task, split_jsonl
from core.llm.constants import (
    SUMMARY_MODEL,
    SUMMARY_REASONING,)

logger = logging.getLogger(__name__)

def main():

    load_dotenv()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

     # ------------
    # DEFINE ARGUMENTS
    # ------------

    # allow command line arguments to specify the fiscal year

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--fiscal-year",
        type=int,
        default=2025,
    )

    args = parser.parse_args()

    logger.info("Generating summarization batch: fiscal_year=%d", args.fiscal_year)

    # ------------
    # DEFINE PROMPT AND OUTPUT PATHS
    # ------------

    prompt = load_prompt("summarization/grant_summary")

    logger.info("Loaded prompt for summarization.")

    output_dir = Path("outputs") / "llm" / "summarization"

    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / f"batch_tasks_{args.fiscal_year}.jsonl"

    # -----------
    # FETCH DATA FROM DATABASE AND WRITE TO JSONL
    # -----------

    try:

        conn = get_db_connection()
        cur = conn.cursor()

        logger.info("Connected to PostgreSQL database.")


        logger.info("Building OpenAI batch tasks...")

        stats = build_classification_batch_task(
            cur=cur,
            output_path=output_path,
            prompt=prompt,
            model=SUMMARY_MODEL,
            reasoning=SUMMARY_REASONING,
            fiscal_year=args.fiscal_year,
        )

        logger.info("Batch task generation complete.")

        conn.close()

        logger.info("Splitting JSONL file into smaller parts...")

        parts = split_jsonl(input_path=output_path, output_dir=output_dir / "split")

        logger.info("Split JSONL file into %d parts.", len(parts))

        logger.info("Batch statistics: %s", stats)
        logger.info(
        "Classification batch generation complete. Output written to %s",
        output_dir,
        )
    except Exception:
        logger.exception("Error during summarization batch generation.")
        raise
    finally:
        if conn:
            conn.close()
            logger.info("Database connection closed.")


if __name__ == "__main__":
    main()
