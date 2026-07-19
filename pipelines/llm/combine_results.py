from pathlib import Path
import argparse

from core.llm.batch import combine_jsonl


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--batch-dir",
        type=Path,
        required=True,
        help="Directory containing parsed batch results.",
    )

    args = parser.parse_args()

    batch_dir = args.batch_dir

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

    print(f"Combined {len(input_paths)} files into {output_path}")


if __name__ == "__main__":
    main()
