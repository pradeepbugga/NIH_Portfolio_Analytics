import logging
import argparse

from core.logging_config import configure_logging

from core.embedding.embedding_job import run_embedding_job, run_summary_embedding_job
from core.embedding.config import EmbeddingConfig

logger = logging.getLogger(__name__)


def main():
    configure_logging()

    logger.info("Starting embedding job.")

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Generate embeddings from AI summaries instead of title/abstract.",
    )
    args = parser.parse_args()

    try:
        if args.summary:
            logger.info("Running embedding job for AI summaries.")
            cfg = EmbeddingConfig(
                text_recipe="AI_summary",
                batch_size=64,  # You can tweak this if memory usage differs for summaries
            )
            run_summary_embedding_job(cfg)
        else:
            logger.info("Running embedding job for grant titles and abstracts.")
            cfg = EmbeddingConfig()
            run_embedding_job(cfg)

        logger.info("Embedding job completed successfully.")

    except Exception:
        logger.exception("Embedding job failed.")


if __name__ == "__main__":
    main()
