from dataclasses import dataclass
import torch

# pubmedbert is best for embedding biomedical text, such as PubMed abstracts and titles
# we are embedding combined title and abstract of grants


@dataclass(frozen=True)
class EmbeddingConfig:
    model_name: str = "NeuML/pubmedbert-base-embeddings"
    embedding_dim: int = 768
    batch_size: int = 64
    device: str = "cuda" if torch.cuda.is_available() else "cpu"
    text_recipe: str = "title+abstract"
    normalization: str = "l2"
    embedding_version: int = 1
