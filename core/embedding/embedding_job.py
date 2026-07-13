#embedding_job.py
#this script runs the embedding job for NIH grants, generating and persisting embeddings for grants that need to be embedded

from tqdm import tqdm
from core.embedding.config import EmbeddingConfig
from core.embedding.model import load_model, embed_batch
from core.embedding.selection import stream_grants_to_embed, stream_summaries_to_embed
from core.embedding.persistence import upsert_embedding, count_grants_to_embed, upsert_summary_embedding, count_summaries_to_embed
from core.db.connection import get_db_connection

def run_embedding_job(cfg: EmbeddingConfig):
    read_conn = get_db_connection()
    write_conn = get_db_connection()

    #server-side cursor for streaming large result sets
    read_cur = read_conn.cursor(name = "embed_cursor")
    read_cur.itersize = 100

    #cursor for writing embeddings to the database
    write_cur = write_conn.cursor()

    #cursor for progress bar
    count_cur = write_conn.cursor()


    try:


        stream_grants_to_embed(read_cur)
        

        model = load_model(cfg.model_name, cfg.device)

        texts, ids, hashes = [], [], []

        total = count_grants_to_embed(count_cur)

        embedded_count = 0

        pbar = tqdm(total=total, desc="Embedding grants", unit = "grants")
        


        # iterate over the grants that need to be embedded
        for grant_id, title, abstract, content_hash in read_cur:
            texts.append(f"{title.strip()} {abstract.strip()}")
            ids.append(grant_id)
            hashes.append(content_hash)

            if len(texts) == cfg.batch_size:
                vectors = embed_batch(model, texts)
                for gid, h, v in zip(ids, hashes, vectors):
                    upsert_embedding(write_cur, gid, h, cfg, v)
                write_conn.commit()

                embedded_count += len(ids)
                pbar.update(len(ids))

                texts.clear(); 
                ids.clear(); 
                hashes.clear()

        # embed any remaining grants that didn't fill a complete batch
        if texts:
            vectors = embed_batch(model, texts)
            for gid, h, v in zip(ids, hashes, vectors):
                upsert_embedding(write_cur, gid, h, cfg, v)
            write_conn.commit()

            embedded_count += len(ids)
            pbar.update(len(ids))

        pbar.close()
        
        print(f"✅ Embedding job completed. Total grants embedded/updated: {embedded_count}")

    finally:

        write_cur.close()
        read_cur.close()
        write_conn.close()
        read_conn.close()
        count_cur.close()





def run_summary_embedding_job(cfg: EmbeddingConfig):
    read_conn = get_db_connection()
    write_conn = get_db_connection()

    # Server-side cursor for safe processing of large datasets
    read_cur = read_conn.cursor(name="embed_summary_cursor")
    read_cur.itersize = 100

    write_cur = write_conn.cursor()
    count_cur = write_conn.cursor()

    # Stream out stale/missing summaries
    stream_summaries_to_embed(read_cur)
    
    model = load_model(cfg.model_name, cfg.device)

    texts, ids, hashes = [], [], []
    total = count_summaries_to_embed(count_cur)
    total_processed = 0

    pbar = tqdm(total=total, desc="Embedding summaries", unit="summaries")
     
    for grant_id, two_sentence_summary, content_hash in read_cur:
        texts.append(two_sentence_summary.strip())
        ids.append(grant_id)
        hashes.append(content_hash)

        if len(texts) == cfg.batch_size:
            vectors = embed_batch(model, texts)
            for gid, h, v in zip(ids, hashes, vectors):
                upsert_summary_embedding(write_cur, gid, h, cfg, v)
            write_conn.commit()
            pbar.update(len(ids))
            total_processed += len(ids)
            texts.clear(); ids.clear(); hashes.clear()

    # Empty out the trailing data batch
    if texts:
        vectors = embed_batch(model, texts)
        for gid, h, v in zip(ids, hashes, vectors):
            upsert_summary_embedding(write_cur, gid, h, cfg, v)
        write_conn.commit()
        pbar.update(len(ids))
        total_processed += len(ids)

    pbar.close()
    print(f"✅ Embedding job completed. Total summaries processed: {total_processed}")

    write_cur.close()
    read_cur.close()
    count_cur.close()
    write_conn.close()
    read_conn.close()