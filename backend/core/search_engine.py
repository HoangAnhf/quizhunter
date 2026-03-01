from typing import List, Optional

from backend.schemas.exam import Exam, Question, SearchResult
from backend.models.embedding_model import EmbeddingModel
from backend.database.vector_store import VectorStore
from backend.database.exam_store import ExamStore
from config import TOP_K_RESULTS


class SearchEngine:
    """Semantic search engine sử dụng Sentence-Transformers + FAISS."""

    def __init__(self):
        self.embedding_model = EmbeddingModel()
        self.vector_store = VectorStore(dimension=self.embedding_model.dimension)
        self.exam_store = ExamStore()

    def index_exam(self, exam: Exam):
        """Tạo embedding và index cho 1 đề thi."""
        if not exam.questions:
            return

        texts = [q.content for q in exam.questions]
        # Thêm title + subject vào context
        texts.append(f"{exam.title} {exam.subject}")

        vectors = self.embedding_model.encode(texts)
        self.vector_store.add(exam.id, vectors)

    def reindex_all(self):
        """Rebuild toàn bộ index từ kho đề."""
        self.vector_store.clear()
        exams = self.exam_store.get_all_exams_unfiltered()
        for exam in exams:
            self.index_exam(exam)

    def search(
        self,
        query: str,
        subject: Optional[str] = None,
        difficulty: Optional[str] = None,
        question_type: Optional[str] = None,
        top_k: int = TOP_K_RESULTS,
    ) -> List[SearchResult]:
        # Đảm bảo index đã được build
        if self.vector_store.total_vectors == 0:
            self.reindex_all()
            # Nếu vẫn rỗng thì không có đề nào
            if self.vector_store.total_vectors == 0:
                return []

        # Tăng search count
        self.exam_store.increment_search_count()

        # Encode query
        query_vector = self.embedding_model.encode_single(query)

        # Tìm trong vector store
        raw_results = self.vector_store.search(query_vector, top_k=top_k * 2)

        # Lấy chi tiết exam và áp dụng bộ lọc
        results = []
        for exam_id, score in raw_results:
            exam = self.exam_store.get_by_id(exam_id)
            if exam is None:
                continue

            # Áp dụng filters
            if subject and exam.subject != subject:
                continue
            if difficulty and exam.difficulty != difficulty:
                continue
            if question_type:
                q_types = {q.question_type for q in exam.questions}
                if question_type not in q_types:
                    continue

            # Tìm câu hỏi khớp nhất trong đề
            matched = self._find_matched_questions(query, exam.questions, top_n=3)

            # Normalize score về 0-1
            normalized_score = max(0.0, min(1.0, (score + 1) / 2))

            results.append(SearchResult(
                exam=exam,
                score=round(normalized_score, 3),
                matched_questions=matched,
            ))

            if len(results) >= top_k:
                break

        return results

    def _find_matched_questions(
        self, query: str, questions: List[Question], top_n: int = 3
    ) -> List[Question]:
        """Tìm các câu hỏi khớp nhất với query trong 1 đề."""
        if not questions:
            return []

        texts = [q.content for q in questions]
        q_vectors = self.embedding_model.encode(texts)
        query_vec = self.embedding_model.encode_single(query)

        # Cosine similarity
        import numpy as np
        q_norms = np.linalg.norm(q_vectors, axis=1, keepdims=True)
        q_norms[q_norms == 0] = 1
        q_vectors_norm = q_vectors / q_norms

        query_norm = np.linalg.norm(query_vec)
        if query_norm > 0:
            query_vec_norm = query_vec / query_norm
        else:
            query_vec_norm = query_vec

        scores = q_vectors_norm @ query_vec_norm

        # Lấy top_n
        top_indices = np.argsort(scores)[::-1][:top_n]
        return [questions[i] for i in top_indices]
