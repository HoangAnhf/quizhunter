import json
import threading
from typing import List, Optional
from pathlib import Path

from backend.schemas.exam import Exam
from config import EXAM_DB_PATH


class ExamStore:
    """Quản lý CRUD kho đề thi, lưu dưới dạng JSON file."""

    _lock = threading.Lock()

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = Path(db_path) if db_path else EXAM_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.db_path.exists():
            self._write_data({"exams": [], "total_searches": 0})

    def _read_data(self) -> dict:
        with self._lock:
            with open(self.db_path, "r", encoding="utf-8") as f:
                return json.load(f)

    def _write_data(self, data: dict):
        with self._lock:
            with open(self.db_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

    def save(self, exam: Exam) -> str:
        data = self._read_data()
        # Kiểm tra trùng ID
        for i, e in enumerate(data["exams"]):
            if e["id"] == exam.id:
                data["exams"][i] = exam.to_dict()
                self._write_data(data)
                return exam.id

        data["exams"].append(exam.to_dict())
        self._write_data(data)
        return exam.id

    def get_all(
        self,
        subject: Optional[str] = None,
        difficulty: Optional[str] = None,
        page: int = 1,
        per_page: int = 10,
    ) -> List[Exam]:
        data = self._read_data()
        exams = [Exam.from_dict(e) for e in data["exams"]]

        if subject:
            exams = [e for e in exams if e.subject == subject]
        if difficulty:
            exams = [e for e in exams if e.difficulty == difficulty]

        # Sắp xếp theo ngày tạo mới nhất
        exams.sort(key=lambda e: e.created_at, reverse=True)

        # Phân trang
        start = (page - 1) * per_page
        end = start + per_page
        return exams[start:end]

    def get_by_id(self, exam_id: str) -> Optional[Exam]:
        data = self._read_data()
        for e in data["exams"]:
            if e["id"] == exam_id:
                return Exam.from_dict(e)
        return None

    def delete(self, exam_id: str) -> bool:
        data = self._read_data()
        original_len = len(data["exams"])
        data["exams"] = [e for e in data["exams"] if e["id"] != exam_id]
        if len(data["exams"]) < original_len:
            self._write_data(data)
            return True
        return False

    def count(
        self,
        subject: Optional[str] = None,
        difficulty: Optional[str] = None,
    ) -> int:
        data = self._read_data()
        exams = data["exams"]

        if subject:
            exams = [e for e in exams if e.get("subject") == subject]
        if difficulty:
            exams = [e for e in exams if e.get("difficulty") == difficulty]

        return len(exams)

    def get_stats(self) -> dict:
        data = self._read_data()
        exams = data["exams"]

        subjects = {}
        difficulties = {}
        total_questions = 0

        for e in exams:
            sub = e.get("subject", "Khác")
            diff = e.get("difficulty", "co_ban")
            subjects[sub] = subjects.get(sub, 0) + 1
            difficulties[diff] = difficulties.get(diff, 0) + 1
            total_questions += len(e.get("questions", []))

        return {
            "total_exams": len(exams),
            "total_questions": total_questions,
            "subjects": subjects,
            "difficulties": difficulties,
            "total_searches": data.get("total_searches", 0),
        }

    def increment_search_count(self):
        data = self._read_data()
        data["total_searches"] = data.get("total_searches", 0) + 1
        self._write_data(data)

    def get_all_exams_unfiltered(self) -> List[Exam]:
        """Lấy toàn bộ đề thi không phân trang (dùng cho indexing)."""
        data = self._read_data()
        return [Exam.from_dict(e) for e in data["exams"]]
