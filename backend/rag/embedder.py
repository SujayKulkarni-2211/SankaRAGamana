import os
from typing import List

import torch
from sentence_transformers import SentenceTransformer


class Embedder:
    _instance: SentenceTransformer = None

    @classmethod
    def get(cls) -> SentenceTransformer:
        if cls._instance is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
            cls._instance = SentenceTransformer(
                "intfloat/multilingual-e5-small",
                device=device,
                cache_folder=os.getenv("MODEL_CACHE", "model_cache"),
            )
        return cls._instance

    @classmethod
    def is_loaded(cls) -> bool:
        return cls._instance is not None

    def embed_query(self, text: str) -> List[float]:
        # CRITICAL: e5 requires "query: " prefix for queries
        return self.get().encode(f"query: {text}").tolist()
