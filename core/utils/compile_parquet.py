import os
import polars as pl
from pathlib import Path

from core.db.connection import get_db_connection


def compile_grant_text_warehouse():
    print("🔄 Connecting to PostgreSQL database...")
    conn = get_db_connection()

    cur = conn.cursor(name="grant_text_cursor")

    # server-side cursor to avoid loading all rows into memory at once

    cur.itersize = (
        10000  # Fetch 10,000 rows at a time to avoid loading everything into memory
    )

    query = """
        SELECT 
            rg.grant_id,
            rg.project_title,
            rg.abstract
        FROM ResearchGrants rg;
    """

    output_path = Path("./data/grant_text_warehouse.parquet")

    print("📦 Executing query to fetch grant texts...")
    cur.execute(query)

    schema = {"grant_id": pl.String, "project_title": pl.String, "abstract": pl.String}

    writer = None  # Initialize writer to None
    total_processed = 0

    print("Starting to process and write grant texts in batches...")
    try:
        while True:
            rows = cur.fetchmany(cur.itersize)
            if not rows:
                break  # Exit loop if no more rows

            chunk_df = pl.DataFrame(rows, schema=schema, orient="row")

            # 2. Combine title and abstract for the Cross-Encoder
            processed_chunk = chunk_df.with_columns(
                [
                    (
                        pl.lit("Title: ")
                        + pl.col("project_title").fill_null("")
                        + pl.lit(" | Abstract: ")
                        + pl.col("abstract").fill_null("")
                    ).alias("text")
                ]
            ).select(["grant_id", "text"])

            # 3. Write to Parquet in append mode
            if writer is None:
                # We extract the Arrow schema directly from our processed Polars frame structure
                writer = processed_chunk.to_arrow().to_batches()[0].schema
                import pyarrow.parquet as pq

                parquet_writer = pq.ParquetWriter(
                    str(output_path), writer, compression="snappy"
                )

            # Stream append this processed chunk's Arrow RecordBatch straight onto disk storage
            for batch in processed_chunk.to_arrow().to_batches():
                parquet_writer.write_batch(batch)

            total_processed += len(rows)
            print(f"💾 Flushed {total_processed} total records to disk...")

    finally:
        if writer is not None:
            parquet_writer.close()
        cur.close()
        conn.close()

    print(
        f"✨ Parquet text warehouse successfully generated at: {output_path} with {total_processed} records."
    )


if __name__ == "__main__":
    compile_grant_text_warehouse()
