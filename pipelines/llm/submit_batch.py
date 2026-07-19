from openai import OpenAI
from pathlib import Path
import argparse
import json
from dotenv import load_dotenv


def main():
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

    batch_dir = args.batch_dir

    manifest = []

    for jsonl_path in sorted(batch_dir.glob("*.jsonl")):

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

        print(
            f"Submitted batch for {jsonl_path.name}: file_id={batch_file.id}, batch_id={batch.id}"
        )

    # Write manifest to JSON file
    manifest_path = batch_dir / "batch_manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=4)

    print(f"Batch submission manifest written to {manifest_path}")


if __name__ == "__main__":
    main()
