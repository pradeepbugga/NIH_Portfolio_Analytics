import modal

# look up the class and its methods by name
Reranker_cls = modal.Cls.from_name("nih-reranker", "Reranker")
reranker = Reranker_cls()

rerank_fn = reranker.rerank_batch
rerank_test = reranker.debug_score

# standalone function for distributed reranking

distributed_rerank_fn = modal.Function.from_name("nih-reranker", "distributed_rerank")
