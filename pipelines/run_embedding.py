#this script runs the embedding job for NIH grants, generating and persisting embeddings for grants that need to be embedded

import logging
import sys

from core.embedding.embedding_job import run_embedding_job
from core.embedding.config import EmbeddingConfig


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )

    try:
        run_embedding_job(EmbeddingConfig())
    except Exception:
        logging.exception("Embedding job failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
