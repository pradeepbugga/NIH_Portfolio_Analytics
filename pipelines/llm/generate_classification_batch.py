import argparse
from pathlib import Path

import logging
from core.logging_config import configure_logging

from dotenv import load_dotenv

from core.db.connection import get_db_connection
from core.llm.prompt_loader import load_prompt
from core.llm.batch import build_classification_batch_task, split_jsonl
from core.llm.constants import (
    CATEGORIES,
    CLASSIFICATION_MODEL,
    CLASSIFICATION_REASONING,
)

logger = logging.getLogger(__name__)


def main():
    configure_logging()

    load_dotenv()

    # ------------
    # DEFINE ARGUMENTS
    # ------------

    # allow command line arguments to specify the classification category and fiscal year
    # classification categories can be "research_tool", "clinical", "diagnostic", "therapeutic",
    # "research_infrastructure", "observational_epidemiology", "education", or "mechanistic"

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--category",
        required=True,
        choices=CATEGORIES,
        help="Classification category (e.g. research_tool)",
    )

    parser.add_argument(
        "--fiscal-year",
        type=int,
        default=2025,
    )

    args = parser.parse_args()

    logger.info(
        "Generating classification batch: category=%s, fiscal_year=%d",
        args.category,
        args.fiscal_year,
    )

    # ------------
    # DEFINE PROMPT AND OUTPUT PATHS
    # ------------

    prompt = load_prompt(f"classification/{args.category}")

    logger.info("Loaded prompt for category: %s", args.category)

    output_dir = Path("outputs") / "llm" / "classification" / args.category

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
            model=CLASSIFICATION_MODEL,
            reasoning=CLASSIFICATION_REASONING,
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
        logger.exception("Error during classification batch generation.")
        raise
    finally:
        if conn:
            conn.close()
            logger.info("Database connection closed.")


if __name__ == "__main__":
    main()
