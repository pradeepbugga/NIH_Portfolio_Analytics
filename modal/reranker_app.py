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
    volumes={"/model":volume},  
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
