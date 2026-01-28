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
)

volume = modal.Volume.from_name("reranker-models")

@app.cls(
    gpu="A10G",
    image=image,
    volumes={"/model":volume},  
    timeout=60
)

class Reranker:
    model_path: str = modal.parameter(default = "/model/v3")

    @modal.enter()
    def load_model(self):
        self.model = CrossEncoder(self.model_path, device="cuda")
            

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
