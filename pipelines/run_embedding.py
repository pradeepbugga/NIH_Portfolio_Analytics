# this script runs the embedding job for NIH grants, generating and persisting embeddings for grants that need to be embedded

import logging
import sys

from core.embedding.embedding_job import run_embedding_job, run_summary_embedding_job
from core.embedding.config import EmbeddingConfig


def main() -> None:

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Generate embeddings from AI summaries instead of title/abstract.",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )

  
    try:
        if args.summary:
            cfg = EmbeddingConfig(
                text_recipe="AI_summary",
                batch_size=64,  # You can tweak this if memory usage differs for summaries
            )
            run_summary_embedding_job(summary_cfg)
        else:
            cfg = EmbeddingConfig()
            run_embedding_job(cfg)
    except Exception:
        logging.exception("Embedding job failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
