import modal

rerank_fn = modal.Function.from_name("nih-reranker", "Reranker.rerank_batch")


distributed_rerank_fn = modal.Function.from_name("nih-reranker", "distributed_rerank")

rerank_test = modal.Function.from_name("nih-reranker", "Reranker.debug_score")
