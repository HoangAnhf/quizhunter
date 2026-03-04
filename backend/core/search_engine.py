from typing import List, Optional
import numpy as np

from backend.schemas.exam import Exam, Question, SearchResult
from backend.models.embedding_model import EmbeddingModel
from backend.database.vector_store import VectorStore
from backend.database.mysql_store import MySQLExamStore
from config import TOP_K_RESULTS


class SearchEngine:
    """Semantic search engine sử dụng Sentence-Transformers + FAISS."""

    def __init__(self):
        self.embedding_model = EmbeddingModel()
        self.vector_store = VectorStore(dimension=self.embedding_model.dimension)
        self.exam_store = MySQLExamStore()

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

    def _parse_query_hints(self, query: str):
        """Phân tích query để trích xuất gợi ý môn học / lớp."""
        import re
        from config import VI_SUBJECTS

        hint_subject = None
        hint_grade = None

        q_lower = query.lower().strip()

        # Map keyword -> subject
        kw_map = {
            "toan": "Toán học", "toán": "Toán học",
            "ly": "Vật lý", "lý": "Vật lý", "vat ly": "Vật lý", "vật lý": "Vật lý",
            "hoa": "Hóa học", "hoá": "Hóa học", "hóa": "Hóa học", "hoa hoc": "Hóa học",
            "sinh": "Sinh học", "sinh hoc": "Sinh học",
            "su": "Lịch sử", "sử": "Lịch sử", "lich su": "Lịch sử",
            "dia": "Địa lý", "địa": "Địa lý", "dia ly": "Địa lý",
            "anh": "Tiếng Anh", "tieng anh": "Tiếng Anh",
            "van": "Ngữ văn", "văn": "Ngữ văn", "ngu van": "Ngữ văn",
            "tin": "Tin học", "tin hoc": "Tin học",
            "gdcd": "GDCD",
        }
        for kw, subj in kw_map.items():
            if kw in q_lower:
                hint_subject = subj
                break

        # Tìm số lớp: "lop 9", "lớp 9", hoặc chỉ số đứng riêng
        m = re.search(r'(?:lop|lớp)\s*(\d{1,2})', q_lower)
        if m:
            hint_grade = int(m.group(1))
        else:
            # Số đứng riêng (1-12) nếu có subject hint
            m = re.search(r'\b(\d{1,2})\b', q_lower)
            if m and hint_subject:
                val = int(m.group(1))
                if 1 <= val <= 12:
                    hint_grade = val

        return hint_subject, hint_grade

    def search(
        self,
        query: str,
        subject: Optional[str] = None,
        difficulty: Optional[str] = None,
        question_type: Optional[str] = None,
        grade: Optional[int] = None,
        top_k: int = TOP_K_RESULTS,
    ) -> List[SearchResult]:
        # Tăng search count
        self.exam_store.increment_search_count(query=query)

        # Phân tích query hints
        hint_subject, hint_grade = self._parse_query_hints(query)
        if not subject and hint_subject:
            subject = hint_subject
        if not grade and hint_grade:
            grade = hint_grade

        # ── 1. Semantic search (FAISS) ──
        semantic_results = []
        if self.vector_store.total_vectors == 0:
            self.reindex_all()

        if self.vector_store.total_vectors > 0:
            query_vector = self.embedding_model.encode_single(query)
            raw_results = self.vector_store.search(query_vector, top_k=top_k * 3)

            seen_ids = set()
            for exam_id, score in raw_results:
                if exam_id in seen_ids:
                    continue
                seen_ids.add(exam_id)

                exam = self.exam_store.get_by_id(exam_id)
                if exam is None:
                    continue

                if subject and exam.subject != subject:
                    continue
                if difficulty and exam.difficulty != difficulty:
                    continue
                if question_type:
                    q_types = {q.question_type for q in exam.questions}
                    if question_type not in q_types:
                        continue
                if grade and exam.grade and exam.grade != grade:
                    continue

                matched = self._find_matched_questions(query, exam.questions, top_n=3)
                normalized_score = max(0.0, min(1.0, (score + 1) / 2))

                semantic_results.append(SearchResult(
                    exam=exam,
                    score=round(normalized_score, 3),
                    matched_questions=matched,
                ))

                if len(semantic_results) >= top_k:
                    break

        # ── 2. Keyword fallback (MySQL) nếu semantic trả ít kết quả ──
        if len(semantic_results) < top_k:
            try:
                kw_exams, _ = self.exam_store.search_by_code_or_title(
                    query=query, subject=subject, difficulty=difficulty,
                    grade=grade, page=1, per_page=top_k,
                )
                existing_ids = {r.exam.id for r in semantic_results}
                for exam in kw_exams:
                    if exam.id in existing_ids:
                        continue
                    if question_type:
                        q_types = {q.question_type for q in exam.questions}
                        if question_type not in q_types:
                            continue
                    matched = self._find_matched_questions(query, exam.questions, top_n=3) if exam.questions else []
                    semantic_results.append(SearchResult(
                        exam=exam,
                        score=0.5,  # keyword match = mid score
                        matched_questions=matched,
                    ))
                    if len(semantic_results) >= top_k:
                        break
            except Exception:
                pass

        return semantic_results

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
