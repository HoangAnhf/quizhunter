import numpy as np
from pathlib import Path
from typing import List, Tuple, Optional

from config import FAISS_INDEX_PATH


class VectorStore:
    """Quản lý FAISS index cho semantic search."""

    def __init__(self, dimension: int = 384, index_path: Optional[Path] = None):
        try:
            import faiss
            self.faiss = faiss
        except ImportError:
            raise ImportError("Cần cài đặt faiss-cpu: pip install faiss-cpu")

        self.dimension = dimension
        self.index_path = Path(index_path) if index_path else FAISS_INDEX_PATH
        self.index_path.parent.mkdir(parents=True, exist_ok=True)

        self.index = None
        self.id_map: List[str] = []  # Map index position -> exam_id

        self._load_or_create()

    def _load_or_create(self):
        meta_path = self.index_path.with_suffix(".meta.npy")

        if self.index_path.exists() and meta_path.exists():
            self.index = self.faiss.read_index(str(self.index_path))
            self.id_map = list(np.load(str(meta_path), allow_pickle=True))
        else:
            self.index = self.faiss.IndexFlatIP(self.dimension)  # Inner Product (cosine sim sau normalize)
            self.id_map = []

    def save(self):
        self.faiss.write_index(self.index, str(self.index_path))
        meta_path = self.index_path.with_suffix(".meta.npy")
        np.save(str(meta_path), np.array(self.id_map, dtype=object))

    def add(self, exam_id: str, vectors: np.ndarray):
        """Thêm vectors cho 1 đề thi. vectors shape: (n_questions, dimension)"""
        if vectors.ndim == 1:
            vectors = vectors.reshape(1, -1)

        # Normalize cho cosine similarity
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms[norms == 0] = 1
        vectors = vectors / norms

        self.index.add(vectors.astype("float32"))
        self.id_map.extend([exam_id] * vectors.shape[0])
        self.save()

    def search(self, query_vector: np.ndarray, top_k: int = 10) -> List[Tuple[str, float]]:
        """Tìm kiếm top_k vectors gần nhất. Trả về list (exam_id, score)."""
        if self.index.ntotal == 0:
            return []

        if query_vector.ndim == 1:
            query_vector = query_vector.reshape(1, -1)

        # Normalize query
        norm = np.linalg.norm(query_vector)
        if norm > 0:
            query_vector = query_vector / norm

        k = min(top_k * 3, self.index.ntotal)  # Lấy nhiều hơn để deduplicate
        scores, indices = self.index.search(query_vector.astype("float32"), k)

        # Deduplicate theo exam_id, giữ score cao nhất
        seen = {}
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(self.id_map):
                continue
            eid = self.id_map[idx]
            if eid not in seen or score > seen[eid]:
                seen[eid] = float(score)

        # Sắp xếp theo score giảm dần
        results = sorted(seen.items(), key=lambda x: x[1], reverse=True)
        return results[:top_k]

    def remove_by_exam_id(self, exam_id: str):
        """Xóa vectors của 1 đề thi và rebuild index."""
        if not self.id_map:
            return

        keep_indices = [i for i, eid in enumerate(self.id_map) if eid != exam_id]
        if len(keep_indices) == len(self.id_map):
            return  # Không có gì để xóa

        if not keep_indices:
            self.index = self.faiss.IndexFlatIP(self.dimension)
            self.id_map = []
            self.save()
            return

        # Rebuild index
        all_vectors = np.array([self.index.reconstruct(i) for i in keep_indices], dtype="float32")
        self.id_map = [self.id_map[i] for i in keep_indices]
        self.index = self.faiss.IndexFlatIP(self.dimension)
        self.index.add(all_vectors)
        self.save()

    def clear(self):
        self.index = self.faiss.IndexFlatIP(self.dimension)
        self.id_map = []
        self.save()

    @property
    def total_vectors(self) -> int:
        return self.index.ntotal
