
import modal 

rerank_fn = modal.Cls.from_name(
    "nih-reranker",
    "Reranker.rerank_batch"
)