from __future__ import annotations

from functools import lru_cache
import hashlib
import math
import re

from langchain_core.embeddings import Embeddings
from sentence_transformers import SentenceTransformer


@lru_cache(maxsize=4)
def _load_model(model_name: str) -> SentenceTransformer:
    # The lab must remain runnable when the hosted model cannot be downloaded.
    return SentenceTransformer(model_name, local_files_only=True)


class MiniLMEmbeddings(Embeddings):
    def __init__(self, model_name: str):
        try:
            self.model = _load_model(model_name)
        except Exception:
            self.model = None

    @staticmethod
    def _fallback_embed(texts: list[str]) -> list[list[float]]:
        """Create stable hash vectors when MiniLM is unavailable offline."""
        dimension = 384
        vectors: list[list[float]] = []
        for text in texts:
            vector = [0.0] * dimension
            for token in re.findall(r"\w+", text.lower()):
                digest = hashlib.sha256(token.encode("utf-8")).digest()
                index = int.from_bytes(digest[:4], "big") % dimension
                vector[index] += 1.0 if digest[4] % 2 else -1.0
            magnitude = math.sqrt(sum(value * value for value in vector))
            vectors.append([value / magnitude for value in vector] if magnitude else vector)
        return vectors

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if self.model is None:
            return self._fallback_embed(texts)
        embeddings = self.model.encode(texts, normalize_embeddings=True)
        return embeddings.tolist()

    def embed_query(self, text: str) -> list[float]:
        if self.model is None:
            return self._fallback_embed([text])[0]
        embedding = self.model.encode([text], normalize_embeddings=True)
        return embedding[0].tolist()
