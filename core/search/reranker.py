# this script provides functions to rerank documents using a CrossEncoder model

from sentence_transformers import CrossEncoder
import torch 

_model = None

RERANK_MODEL_PATH = "./models/rerankers/v4"
device = "cuda" if torch.cuda.is_available() else "cpu"

# lazy initialization to load the model only once

def get_reranker():
    global _model
    if _model is None:        
        _model = CrossEncoder(RERANK_MODEL_PATH, device=device)
 
    return _model

def rerank(query, docs):
    model = get_reranker()
    inputs = [(query, doc) for doc in docs]
    if device == "cuda":
        with torch.amp.autocast(device_type="cuda"):
            scores = model.predict(inputs)
    else:
        with torch.amp.autocast(device_type="cpu", dtype=torch.bfloat16):
            scores = model.predict(inputs)
    return scores

def rerank_batch(query, docs_list, batch_size=32):
    model = get_reranker()
    all_scores = []

    for i in range(0, len(docs_list), batch_size):
        batch = docs_list[i:i + batch_size]
        inputs = [(query, doc) for doc in batch]

        #using automatic mixed precision (autocast) improves latency
        
        if device == "cuda":
            with torch.no_grad(), torch.amp.autocast(device_type="cuda"):  
                scores = model.predict(inputs)
        else: 
            with torch.no_grad(), torch.amp.autocast(device_type="cpu", dtype=torch.bfloat16):
                scores = model.predict(inputs)
        all_scores.extend(scores)

    return all_scores

# this function warms up the reranker model by running a large batch of dummy data through it
# warm up also improves latency for the first real inference

def warmup_reranker():
    model = get_reranker()
    dummy_query = "warmup"
    dummy_docs = ["warmup"] * 2048   # large batch
    if device == "cuda":
            
        with torch.no_grad(), torch.amp.autocast(device_type="cuda"):
            model.predict(
                [(dummy_query, d) for d in dummy_docs],
                batch_size=32,
                show_progress_bar=False
            )
    else:
        with torch.no_grad(), torch.amp.autocast(device_type="cpu", dtype=torch.bfloat16):
            model.predict(
                [(dummy_query, d) for d in dummy_docs],
                batch_size=32,
                show_progress_bar=False
            )