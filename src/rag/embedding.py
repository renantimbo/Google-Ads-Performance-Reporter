import numpy as np
from sentence_transformers import SentenceTransformer

_DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

_model_cache: dict[str, SentenceTransformer] = {}

def get_model(model_name: str = _DEFAULT_MODEL) -> SentenceTransformer:
    if model_name not in _model_cache:
        _model_cache[model_name] = SentenceTransformer(model_name)
    return _model_cache[model_name]

def embed_text(text: str, model_name: str = _DEFAULT_MODEL) -> np.ndarray:
    model = get_model(model_name)
    vec = model.encode(text, normalize_embeddings=True)
    return np.asarray(vec, dtype=np.float32)

def cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b))
