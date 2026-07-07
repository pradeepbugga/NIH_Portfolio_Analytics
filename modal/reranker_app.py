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
    max_containers=10
)

class Reranker:
    model_path: str = modal.parameter(default = "/model/v5")

    parquet_path: str = modal.parameter(default = "/model/search_assets/grant_text_warehouse.parquet")

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
        import polars as pl

        print("Loading CrossEncoder model...")
        self.model = CrossEncoder(self.model_path, device="cuda", model_kwargs={"torch_dtype": torch.float16})
            
        print(f"Loading Parquet text warehouse from: {self.parquet_path}")
        try:
            df = pl.read_parquet(self.parquet_path, columns=["grant_id", "text"])
            self.text_lookup = dict(zip(df["grant_id"], df["text"]))
            print(f"Loaded {len(self.text_lookup)} grant texts into memory.")

        except Exception as e:
            print(f"Error loading Parquet file: {e}")
            self.text_lookup = {}

    @modal.method()
    def rerank_batch(self, query: str, grant_ids: list, batch_size=512):
        # intercept speculative ping immediately 
        if query == "[WARM_UP_PING]":
            print("Received warm-up ping, waking up container...")
            return []  # return an empty list for warm-up pings
        
        if not grant_ids:
            print("No grant ids to rerank, returning empty list...")
            return []

        print(f"📦 RECEIVED {len(grant_ids)} IDs FROM FASTAPI")
        print(f"👉 Sample incoming IDs: {grant_ids[:5]}")
            
       # 🟢 Construct pairs while enforcing absolute alignment with the input order
        inputs = []
        missing_count = 0
        
        for gid in grant_ids:
            clean_id = str(gid).strip().upper()
            if clean_id in self.text_lookup:
                inputs.append((query, self.text_lookup[clean_id]))
            else:
                inputs.append((query, "Missing abstract text data."))  # Fallback keeps array indices aligned
                missing_count += 1

        if missing_count > 0:
            print(f"⚠️ Warning: {missing_count} / {len(grant_ids)} IDs were missing from the Parquet map and given fallbacks.")

        # Start your GPU monitor thread
        threading.Thread(
            target=self._monitor_gpu,
            daemon=True
        ).start()

        t0 = time.perf_counter()

        # Execute mixed-precision batch inference
        with torch.no_grad(), torch.amp.autocast("cuda"):  
            scores = self.model.predict(
                inputs, 
                batch_size=batch_size,
                show_progress_bar=False,
                convert_to_numpy=True,
                max_length=256  # 🟢 Limit token length to boost parallel chunk throughput
            )

        elapsed = time.perf_counter() - t0

        print(f"Elapsed: {elapsed:.2f} sec")
        print(f"Pairs/sec: {len(inputs)/elapsed:.1f}")
            
        # 🟢 Safely handle converting output to a plain list
        if hasattr(scores, "tolist"):
            return scores.tolist()
        return list(scores)

@app.function()
def distributed_rerank(query: str, all_grant_ids: list, chunk_size: int = 5000) -> list:
    """
    Orchestrator function: Splits IDs and scatters chunks across GPU workers.
    """

    if not all_grant_ids:
        return []

    chunks = [
        all_grant_ids[i:i + chunk_size]
        for i in range(0, len(all_grant_ids), chunk_size)
    ]

    print(
        f"📡 Horizontal Scaling: Scattering {len(chunks)} chunks across GPU workers..."
    )

    reranker = Reranker()

    jobs = []

    for chunk in chunks:
        job = reranker.rerank_batch.spawn(
            query,
            chunk,
            512
        )
        jobs.append(job)

    all_scores = []

    for job in jobs:
        chunk_scores = job.get()
        all_scores.extend(chunk_scores)

    print(
        f"🤲 Gathered all scores. Total count: {len(all_scores)}"
    )

    return all_scores
    
