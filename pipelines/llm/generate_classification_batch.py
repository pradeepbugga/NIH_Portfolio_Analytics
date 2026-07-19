import argparse
from pathlib import Path

from dotenv import load_dotenv

from core.db.connection import get_db_connection
from core.llm.prompt_loader import load_prompt
from core.llm.batch import build_classification_batch_task, split_jsonl
from core.llm.constants import (
    CATEGORIES,
    CLASSIFICATION_MODEL,
    CLASSIFICATION_REASONING,
)


def main():

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

    # ------------
    # DEFINE PROMPT AND OUTPUT PATHS
    # ------------

    prompt = load_prompt(f"classification/{args.category}")

    output_dir = Path("outputs") / "llm" / "classification" / args.category

    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / f"batch_tasks_{args.fiscal_year}.jsonl"

    # -----------
    # FETCH DATA FROM DATABASE AND WRITE TO JSONL
    # -----------

    conn = get_db_connection()
    cur = conn.cursor()

    stats = build_classification_batch_task(
        cur=cur,
        output_path=output_path,
        prompt=prompt,
        model=CLASSIFICATION_MODEL,
        reasoning=CLASSIFICATION_REASONING,
        fiscal_year=args.fiscal_year,
    )

    conn.close()

    parts = split_jsonl(input_path=output_path, output_dir=output_dir / "split")

    print(stats)
    print(f"Created {len(parts)} split JSONL files in {output_dir / 'split'}")


if __name__ == "__main__":
    main()
