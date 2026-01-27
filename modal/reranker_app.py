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
        "numpy"
    )
    .copy_local_dir(
        "./models/rerankers/v3",
        "/model"
    )
)

@app.cls(
    gpu="A10G",
    image=image,
    timeout=60
)

class Reranker:
    def __enter__(self):
        self.model = CrossEncoder("/model", device="cuda")
        self._warmup()

    def warmup(self):
        dummy_query = "warmup"
        dummy_docs = ["warmup"] * 128   # large batch
                 
        with torch.no_grad(), torch.amp.autocast("cuda"):
            self.model.predict(
                [(dummy_query, d) for d in dummy_docs],
                batch_size=32,
                show_progress_bar=False
            )

    @modal.method()
    def rerank_batch(self, query, docs_list, batch_size=128):
        inputs = [(query, doc) for doc in docs_list]    

        with torch.no_grad(), torch.amp.autocast("cuda"):  
            scores = self.model.predict(
                inputs, 
                batch_size = batch_size,
                show_progress_bar = False,
                convert_to_numpy = True)
            
        return scores.tolist()
