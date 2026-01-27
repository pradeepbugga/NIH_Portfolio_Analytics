
from modal import function

_reranker = Function.lookup("nih-reranker", "Reranker")

def modal_rerank(query, docs_list, batch_size):
    return _reranker.rerank_batch(query, docs_list, batch_size)