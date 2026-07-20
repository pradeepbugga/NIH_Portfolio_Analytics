from sentence_transformers import SentenceTransformer


def load_model(model_name: str, device: str) -> SentenceTransformer:
    return SentenceTransformer(model_name, device=device)


def embed_batch(model, texts):
    return model.encode(texts, normalize_embeddings=True, convert_to_numpy=True).astype(
        "float32"
    )
