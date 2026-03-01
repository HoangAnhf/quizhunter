from typing import List
import numpy as np

from config import EMBEDDING_MODEL


class EmbeddingModel:
    """Load và quản lý model embedding cho semantic search."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._model = None
        return cls._instance

    def _load_model(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(EMBEDDING_MODEL)
            except ImportError:
                raise ImportError(
                    "Cần cài đặt sentence-transformers: pip install sentence-transformers"
                )

    def encode(self, texts: List[str]) -> np.ndarray:
        self._load_model()
        embeddings = self._model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
        return embeddings.astype("float32")

    def encode_single(self, text: str) -> np.ndarray:
        return self.encode([text])[0]

    @property
    def dimension(self) -> int:
        self._load_model()
        return self._model.get_sentence_embedding_dimension()
