import os
from typing import Optional

import numpy as np


EMBEDDER_MODE = os.getenv("SCOUT_EMBEDDER", "auto").lower()


_hf_model = None


def _try_hf_model():
    global _hf_model
    if _hf_model is not None:
        return _hf_model
    try:
        from sentence_transformers import SentenceTransformer  # type: ignore

        model_name = os.getenv("SCOUT_HF_MODEL", "all-MiniLM-L6-v2")
        _hf_model = SentenceTransformer(model_name)
        return _hf_model
    except Exception:
        return None


def _hashing_embed(text: str, n_features: int = 768) -> np.ndarray:
    from sklearn.feature_extraction.text import HashingVectorizer
    from sklearn.preprocessing import normalize

    vec = HashingVectorizer(n_features=n_features, alternate_sign=False, norm=None)
    X = vec.transform([text])
    dense = X.toarray().astype("float32")
    dense = normalize(dense, norm="l2")
    return dense[0]


def embed_text(text: str) -> np.ndarray:
    """Return a float32 vector embedding. Prefers HF if available and mode allows, else hashing.
    """
    text = (text or "").strip()
    if not text:
        return np.zeros((768,), dtype="float32")

    if EMBEDDER_MODE in ("auto", "hf"):
        model = _try_hf_model()
        if model is not None:
            try:
                vec = model.encode([text], normalize_embeddings=True)
                return vec[0].astype("float32")
            except Exception:
                pass
    # fallback
    return _hashing_embed(text)


def to_blob(vec: np.ndarray) -> bytes:
    vec = vec.astype("float32")
    return vec.tobytes()


def from_blob(blob: bytes, dim: int) -> np.ndarray:
    return np.frombuffer(blob, dtype="float32", count=dim)

