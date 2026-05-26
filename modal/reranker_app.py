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
        "vllm>=0.6.5"
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
    model_path: str = modal.parameter(default = "/model/v3")

    @modal.enter()
    def load_model(self):
        from vllm import LLM

        self.engine = LLM(
            model=self.model_path,
            task = "score",
            enforce_eager =False,
            max_model_len = 1024
        )


        self.model = CrossEncoder(self.model_path, device="cuda")
            

    @modal.method()
    def rerank_batch(self, query, docs_list):
       
        # format pairs for the model
        outputs = self.engine.score(
            text_1 = query,
            text_2 = docs_list,
        )

        #extract pure float similarity scores from the model output
        scores = [out.outputs.score for out in outputs]
        return scores
