# this script provides functions to rerank documents using a CrossEncoder model
# this script uses Modal AI GPU for accelerated inference

from sentence_transformers import CrossEncoder
import torch 
import modal

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
        "/model":volume,
        "/search_assets": assets_volume
    },    
    timeout=300
)

class Reranker:
    model_path: str = modal.parameter(default = "/model/v5")

    parquet_path: str = modal.parameter(default = "/search_assets/grant_text_warehouse.parquet")

    @modal.enter()
    def load_resources(self):
        import polars as pl

        print("Loading CrossEncoder model...")
        self.model = CrossEncoder(self.model_path, device="cuda")
            
        print(f"Loading Parquet text warehouse from: {self.parquet_path}")
        try:
            df = pl.read_parquet(self.parquet_path, columns=["grant_id", "text"])
            self.text_lookup = dict(zip(df["grant_id"], df["text"]))
            print(f"Loaded {len(self.text_lookup)} grant texts into memory.")

        except Exception as e:
            print(f"Error loading Parquet file: {e}")
            self.text_lookup = {}


    @modal.method()
    def rerank_batch(self, query: str, grant_ids: list, batch_size=128):
        # intercept speculative ping immediately 
        if query == "[WARM_UP_PING]":
            print("Received warm-up ping, waking up container...")
            return []  # return an empty list for warm-up pings
        
        if not grant_ids:
            print("No grant ids to rerank, returning empty list...")
            return []

        print(f"📦 RECEIVED {len(grant_ids)} IDs FROM FASTAPI")
        print(f"👉 Sample incoming IDs: {grant_ids[:5]}")
            
        # 🟢 ADD THIS TEMPORARY DEBUG LOOP HERE:
        parquet_keys = list(self.text_lookup.keys())
        print(f"💾 Total keys in memory lookup: {len(parquet_keys)}")
        if parquet_keys:
            # Wrapped in brackets to reveal any invisible spaces or formatting mismatches
            print(f"💾 Sample Parquet keys in memory: {[f'[{k}]' for k in parquet_keys[:5]]}")
            print(f"👉 Sample incoming keys formatted: {[f'[{str(gid).strip().upper()}]' for gid in grant_ids[:5]]}")
            
        # Print sample keys actually loaded in your Parquet dictionary
        existing_keys = list(self.text_lookup.keys())
        if existing_keys:
            print(f"💾 Sample Parquet keys: {existing_keys[:5]}")

        # hydrate grant ids from the lookup dictionary locally
        docs_list = [self.text_lookup[gid] for gid in grant_ids if gid in self.text_lookup]

        if not docs_list:
            print("⚠️ Match failure: None of the provided grant_ids exist in local Parquet map.")
            return []

        inputs = [(query, doc) for doc in docs_list]    

        with torch.no_grad(), torch.amp.autocast("cuda"):  
            scores = self.model.predict(
                inputs, 
                batch_size = batch_size,
                show_progress_bar = False,
                convert_to_numpy = True)
            
        return scores.tolist()

    
