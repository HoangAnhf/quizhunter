from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Question:
    id: str
    content: str
    options: List[str] = field(default_factory=list)
    answer: str = ""
    question_type: str = "trac_nghiem"  # "trac_nghiem" | "tu_luan" | "bai_tap"
    # Mở rộng — backward-compatible (default None)
    grade: Optional[int] = None           # Lớp 1-12
    topic: Optional[str] = None           # Chủ đề trong môn (VD: "Đạo hàm")
    solution: Optional[str] = None        # Lời giải chi tiết (mở rộng sau)
    comment: Optional[str] = None         # Bình luận (mở rộng sau)
    column_a: Optional[List[str]] = None  # Cột A — dạng nối cột
    column_b: Optional[List[str]] = None  # Cột B — dạng nối cột (đã xáo trộn)

    def to_dict(self) -> dict:
        d = {
            "id": self.id,
            "content": self.content,
            "options": self.options,
            "answer": self.answer,
            "question_type": self.question_type,
        }
        # Chỉ thêm field mở rộng nếu có giá trị (giữ JSON gọn)
        if self.grade is not None:
            d["grade"] = self.grade
        if self.topic is not None:
            d["topic"] = self.topic
        if self.solution is not None:
            d["solution"] = self.solution
        if self.comment is not None:
            d["comment"] = self.comment
        if self.column_a is not None:
            d["column_a"] = self.column_a
        if self.column_b is not None:
            d["column_b"] = self.column_b
        return d

    @staticmethod
    def from_dict(data: dict) -> "Question":
        return Question(
            id=data.get("id", ""),
            content=data.get("content", ""),
            options=data.get("options", []),
            answer=data.get("answer", ""),
            question_type=data.get("question_type", "trac_nghiem"),
            grade=data.get("grade"),
            topic=data.get("topic"),
            solution=data.get("solution"),
            comment=data.get("comment"),
            column_a=data.get("column_a"),
            column_b=data.get("column_b"),
        )


@dataclass
class Exam:
    id: str
    title: str
    subject: str
    difficulty: str  # "co_ban" | "trung_binh" | "nang_cao"
    questions: List[Question] = field(default_factory=list)
    source_file: Optional[str] = None
    created_at: str = ""
    grade: Optional[int] = None  # Lớp 1-12
    exam_code: Optional[str] = None  # Mã đề ngắn, VD: TOAN-8-CB-001

    def to_dict(self) -> dict:
        d = {
            "id": self.id,
            "title": self.title,
            "subject": self.subject,
            "difficulty": self.difficulty,
            "questions": [q.to_dict() for q in self.questions],
            "source_file": self.source_file,
            "created_at": self.created_at,
        }
        if self.grade is not None:
            d["grade"] = self.grade
        if self.exam_code is not None:
            d["exam_code"] = self.exam_code
        return d

    @staticmethod
    def from_dict(data: dict) -> "Exam":
        return Exam(
            id=data.get("id", ""),
            title=data.get("title", ""),
            subject=data.get("subject", ""),
            difficulty=data.get("difficulty", "co_ban"),
            questions=[Question.from_dict(q) for q in data.get("questions", [])],
            source_file=data.get("source_file"),
            created_at=data.get("created_at", ""),
            grade=data.get("grade"),
            exam_code=data.get("exam_code"),
        )


@dataclass
class SearchResult:
    exam: Exam
    score: float
    matched_questions: List[Question] = field(default_factory=list)
