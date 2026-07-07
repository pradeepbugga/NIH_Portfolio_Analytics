# this script provides functions to rerank documents using a CrossEncoder model
# this script uses Modal AI GPU for accelerated inference

from sentence_transformers import CrossEncoder
import torch 
import modal
import threading
import subprocess
import time

app = modal.App("nih-reranker")

image = (
    modal.Image.debian_slim()
    .pip_install(
        "torch",
        "sentence-transformers",
        "transformers",
        "numpy",
        "polars",
        "pyarrow"
    )
)

volume = modal.Volume.from_name("reranker-models")

@app.cls(
    gpu="A10G",
    image=image,
    volumes={
        "/model":volume
    },    
    timeout=300,
    max_containers=10,
    min_containers=10
)

class Reranker:
    model_path = "/model/v5"

    parquet_path = "/model/search_assets/grant_text_warehouse.parquet"

    def _monitor_gpu(self):
        while True:
            try:
                out = subprocess.check_output(
                    [
                        "nvidia-smi",
                        "--query-gpu=utilization.gpu,memory.used,memory.total",
                        "--format=csv,noheader"
                    ],
                    text=True,
                )
                print(f"GPU: {out.strip()}")
            except Exception:
                break

            time.sleep(1)


    @modal.enter()
    def load_resources(self):
        import os
        import polars as pl
        
        # 🟢 Track container identity
        self.container_id = os.environ.get("MODAL_TASK_ID", "local")
        print(f"🔥 CLOUD CONTAINER INITIALIZING: {self.container_id}")
        
        print("Loading CrossEncoder model directly into warm VRAM...")
        self.model = CrossEncoder(self.model_path, device="cuda")
        self.model.model.half()
            
        print(f"[{self.container_id}] Pre-loading text warehouse...")
        try:
            df = pl.read_parquet(self.parquet_path, columns=["grant_id", "text"])
            self.text_lookup = dict(zip(df["grant_id"], df["text"]))
            print(f"[{self.container_id}] Container ready. Loaded {len(self.text_lookup)} keys.")
        except Exception as e:
            print(f"Error loading Parquet file: {e}")
            self.text_lookup = {}

    @modal.method()
    
    def warmup(self):
        dummy_text = next(iter(self.text_lookup.values()))

        inputs = [
            ("warmup query", dummy_text)
            for _ in range(512)
        ]

        with torch.no_grad(), torch.amp.autocast("cuda"):
            self.model.predict(
                inputs,
                batch_size=512,
                max_length=256,
                show_progress_bar=False,
            )

        return True

    @modal.method()
    def rerank_batch(self, query: str, grant_ids: list, batch_size=512):

        t_total = time.perf_counter()

        if not grant_ids:
            print("No grant ids to rerank, returning empty list...")
            return []

        print(f"📦 [{self.container_id}] RECEIVED {len(grant_ids)} IDs FROM FASTAPI")

        #
        # Stage 1: Lookup docs
        #
        t = time.perf_counter()

        docs = [
            self.text_lookup.get(str(gid).strip().upper(), "Missing abstract text data.")
            for gid in grant_ids
        ]

        print(f"Lookup docs: {time.perf_counter() - t:.3f}s")

        missing_count = sum(doc == "Missing abstract text data." for doc in docs)

        if missing_count:
            print(f"⚠️ Missing: {missing_count}")

        #
        # Stage 2: Build input tuples
        #
        t = time.perf_counter()

        inputs = [(query, doc) for doc in docs]

        print(f"Build inputs: {time.perf_counter() - t:.3f}s")

        #
        # Stage 3: CrossEncoder inference
        #
        t = time.perf_counter()

        with torch.no_grad(), torch.amp.autocast("cuda"):
            scores = self.model.predict(
                inputs,
                batch_size=batch_size,
                show_progress_bar=False,
                convert_to_numpy=True,
                max_length=256,
            )

        predict_time = time.perf_counter() - t

        print(f"Predict: {predict_time:.3f}s")
        print(f"Pairs/sec: {len(inputs)/predict_time:.1f}")

        #
        # Stage 4: Convert output
        #
        t = time.perf_counter()

        if hasattr(scores, "tolist"):
            scores = scores.tolist()
        else:
            scores = list(scores)

        print(f"Convert output: {time.perf_counter() - t:.3f}s")

        print(f"Total rerank_batch(): {time.perf_counter() - t_total:.3f}s")

        return scores

@app.function(
    image=image
)
def distributed_rerank(query, all_grant_ids, chunk_size=8000):

    print("🔥 ENTERED DISTRIBUTED RERANK")
    print(len(all_grant_ids))

    t0 = time.perf_counter()
    chunks = [
        all_grant_ids[i:i+chunk_size]
        for i in range(0, len(all_grant_ids), chunk_size)
    ]

    print(f"Launching {len(chunks)} workers")

    t1 = time.perf_counter()
    print(f"Chunking time: {t1 - t0:.2f} sec")

    reranker = Reranker()

    queries = [query] * len(chunks)


    results = reranker.rerank_batch.map(
        queries,
        chunks,
        [512] * len(chunks)
    )

    t2 = time.perf_counter()
    print(f"Reranking time: {t2 - t1:.2f} sec")

    scores = []

    for chunk_scores in results:
        scores.extend(chunk_scores)

    t3 = time.perf_counter()
    print(f"Total time: {t3 - t0:.2f} sec")
    

    return scores    

