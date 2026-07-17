#query_embedding.py
# this script provides functions to embed queries using a SentenceTransformer model
# note: we use pubmedbert again

from sentence_transformers import SentenceTransformer
import torch
from functools import lru_cache


@lru_cache(maxsize=1)
def get_query_encoder():

    device = torch.device(
        "cuda" if torch.cuda.is_available() else "cpu"
    )

    return SentenceTransformer(
        "NeuML/pubmedbert-base-embeddings",
        device=device,
    )

def embed_query(text: str):
    model = get_query_encoder()
    with torch.no_grad():
        return model.encode(
            [text], convert_to_numpy=True,
            normalize_embeddings=True
        )[0]

def warmup_query_encoder():
    model = get_query_encoder()
    with torch.no_grad():
        model.encode(
            ["warmup text for gpu initialization"],
            normalize_embeddings=True,
            show_progress_bar=False
        )
