import modal

Reranker_cls = modal.Cls.from_name("nih-reranker", "Reranker")

# create a reranker instance 
reranker = Reranker_cls()

# access class methods

rerank_fn = reranker.rerank_batch

rerank_test = reranker.debug_score

distributed_rerank_fn = modal.Function.lookup("nih-reranker", "distributed_rerank")
