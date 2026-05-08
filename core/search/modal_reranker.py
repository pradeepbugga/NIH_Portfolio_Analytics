
import modal 

rerank_fn = modal.Function.from_name(
    "nih-reranker",
    "Reranker.rerank_batch"
)