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
    timeout=300
)

class Reranker:
    model_path: str = modal.parameter(default = "/model/v5")

    @modal.enter()
    def load_model(self):
        self.model = CrossEncoder(self.model_path, device="cuda")
            

    @modal.method()
def rerank_batch(self, query, docs_list, batch_size=128):
    import time
    import torch

    # 1. Setup raw input text pairs
    inputs = [(query, doc) for doc in docs_list]    

    # Force a baseline sync so earlier cluster setups don't taint numbers
    torch.cuda.synchronize()
    t_global_start = time.perf_counter()

    # --- PHASE 1: TOKENIZATION (CPU Heavy String Parsing) ---
    t_tok_start = time.perf_counter()
    features = self.model.tokenize(inputs)
    t_tok_end = time.perf_counter()
    print(f"⏱️ [Profiling] Tokenization: {t_tok_end - t_tok_start:.4f}s")

    # --- PHASE 2: H2D DEVICE TRANSFER (Moving data to GPU VRAM) ---
    t_vram_start = time.perf_counter()
    features = {k: v.to("cuda") for k, v in features.items()}
    torch.cuda.synchronize() # Wait until data is fully resting on the VRAM tracks
    t_vram_end = time.perf_counter()
    print(f"⏱️ [Profiling] VRAM Device Transfer: {t_vram_end - t_vram_start:.4f}s")

    # --- PHASE 3: THE RAW GPU FORWARD PASS ---
    # Note: We bypass model.predict() and hit the underlying neural net graph directly
    # to avoid double-tokenization overhead.
    all_scores = []
    
    with torch.no_grad(), torch.amp.autocast("cuda"):  
        t_forward_start = time.perf_counter()
        
        # Since features is a monolithic dict of 17,000 padded tensors, 
        # we slice them into batches to respect your execution batch_size
        num_inputs = len(inputs)
        for i in range(0, num_inputs, batch_size):
            # Slice the input tensors for the current batch
            batch_features = {k: v[i:i + batch_size] for k, v in features.items()}
            
            # Forward pass through the actual underlying PyTorch module
            outputs = self.model.model(**batch_features)
            
            # Pull the raw outputs out (adjusting keys depending on your model signature)
            if hasattr(outputs, "logits"):
                logits = outputs.logits
            else:
                logits = outputs[0] if isinstance(outputs, tuple) else outputs
                
            all_scores.append(logits)
            
        # Wait for every single matrix multiplication chunk to finalize on the CUDA cores
        torch.cuda.synchronize() 
        t_forward_end = time.perf_counter()
        
    print(f"⏱️ [Profiling] Core GPU Forward Pass (Batched): {t_forward_end - t_forward_start:.4f}s")

    # --- PHASE 4: RECONSTRUCTION & SERIALIZATION (GPU -> CPU -> Python List) ---
    t_post_start = time.perf_counter()
    
    # Concat individual batches, move them to the CPU stack, and flatten to float values
    final_tensor = torch.cat(all_scores, dim=0).squeeze(-1)
    scores_list = final_tensor.cpu().float().numpy().tolist()
    
    t_post_end = time.perf_counter()
    print(f"⏱️ [Profiling] Post-Processing / Python List Translation: {t_post_end - t_post_start:.4f}s")
    print(f"🚀 Total container processing time: {time.perf_counter() - t_global_start:.4f}s")
        
    return scores_list