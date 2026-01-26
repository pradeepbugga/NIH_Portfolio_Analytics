#model.py
#this script contains functions for loading a sentence transformer model and generating embeddings for a batch of texts

from sentence_transformers import SentenceTransformer
import numpy as np

def load_model(model_name: str, device: str) -> SentenceTransformer:
    return SentenceTransformer(model_name, device=device)

def embed_batch(model, texts):
    return model.encode(
        texts,
        normalize_embeddings=True,
        convert_to_numpy=True
    ).astype("float32")