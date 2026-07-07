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
    min_containers=0
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

        request_start = time.perf_counter()

        if not grant_ids:
            print("No grant ids to rerank, returning empty list...")
            return []

        print(f"\n📦 [{self.container_id}] RECEIVED {len(grant_ids)} IDs FROM FASTAPI")
        print(f"👉 Sample incoming IDs: {grant_ids[:5]}")

        received_time = time.perf_counter()
        print(
            f"⏱️ Receive/logging time: "
            f"{received_time - request_start:.4f}s"
        )


        # -----------------------------
        # Text lookup
        # -----------------------------
        lookup_start = time.perf_counter()

        docs = [
            self.text_lookup.get(
                str(gid).strip().upper(),
                "Missing abstract text data."
            )
            for gid in grant_ids
        ]

        missing_count = sum(
            1 for doc in docs
            if doc == "Missing abstract text data."
        )

        lookup_end = time.perf_counter()

        print(
            f"📚 Text lookup time: "
            f"{lookup_end - lookup_start:.4f}s"
        )

        if missing_count > 0:
            print(
                f"⚠️ Missing {missing_count}/{len(grant_ids)} IDs"
            )


        # -----------------------------
        # Input construction
        # -----------------------------
        input_start = time.perf_counter()

        inputs = [
            (query, doc)
            for doc in docs
        ]

        input_end = time.perf_counter()

        print(
            f"🔨 Input construction time: "
            f"{input_end - input_start:.4f}s"
        )


        # -----------------------------
        # GPU inference
        # -----------------------------
        inference_start = time.perf_counter()

        with torch.no_grad(), torch.amp.autocast("cuda"):

            scores = self.model.predict(
                inputs,
                batch_size=batch_size,
                show_progress_bar=False,
                convert_to_numpy=True,
                max_length=256
            )

        inference_end = time.perf_counter()

        inference_time = inference_end - inference_start

        print(
            f"🚀 Model inference time: "
            f"{inference_time:.4f}s"
        )

        print(
            f"⚡ Throughput: "
            f"{len(inputs)/inference_time:.1f} pairs/sec"
        )


        # -----------------------------
        # Output conversion
        # -----------------------------
        convert_start = time.perf_counter()

        if hasattr(scores, "tolist"):
            scores = scores.tolist()
        else:
            scores = list(scores)

        convert_end = time.perf_counter()

        print(
            f"📤 Score conversion time: "
            f"{convert_end - convert_start:.4f}s"
        )


        # -----------------------------
        # Total
        # -----------------------------
        total_time = time.perf_counter() - request_start

        print(
            f"🏁 TOTAL rerank_batch time: "
            f"{total_time:.4f}s"
        )

        print(
            f"📊 Breakdown: "
            f"lookup={lookup_end-lookup_start:.3f}s | "
            f"build={input_end-input_start:.3f}s | "
            f"inference={inference_time:.3f}s | "
            f"convert={convert_end-convert_start:.3f}s"
        )

        return scores

@app.function(
    image=image
)
def distributed_rerank(query, all_grant_ids, chunk_size=8000):

    print("🔥 ENTERED DISTRIBUTED RERANK")
    print(len(all_grant_ids))

    total_start = time.perf_counter()

    # ------------------------
    # Chunking
    # ------------------------
    t0 = time.perf_counter()

    chunks = [
        all_grant_ids[i:i+chunk_size]
        for i in range(0, len(all_grant_ids), chunk_size)
    ]

    chunk_time = time.perf_counter() - t0

    print(f"Launching {len(chunks)} workers")
    print(f"Chunking time: {chunk_time:.3f} sec")


    reranker = Reranker()

    queries = [query] * len(chunks)


    # ------------------------
    # GPU execution
    # ------------------------
    rerank_start = time.perf_counter()

    results = reranker.rerank_batch.map(
        queries,
        chunks,
        [512] * len(chunks)
    )


    scores = []

    first_result_time = None

    for chunk_scores in results:

        if first_result_time is None:
            first_result_time = time.perf_counter()
            print(
                f"First worker completed after "
                f"{first_result_time-rerank_start:.3f} sec"
            )

        scores.extend(chunk_scores)


    rerank_time = time.perf_counter() - rerank_start

    print(f"Reranking time: {rerank_time:.3f} sec")


    # ------------------------
    # Total
    # ------------------------
    total_time = time.perf_counter() - total_start

    print(f"Total distributed_rerank time: {total_time:.3f} sec")

    return scores