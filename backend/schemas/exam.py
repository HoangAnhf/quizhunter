from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Question:
    id: str
    content: str
    options: List[str] = field(default_factory=list)
    answer: str = ""
    question_type: str = "trac_nghiem"  # "trac_nghiem" | "tu_luan" | "bai_tap"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "content": self.content,
            "options": self.options,
            "answer": self.answer,
            "question_type": self.question_type,
        }

    @staticmethod
    def from_dict(data: dict) -> "Question":
        return Question(
            id=data.get("id", ""),
            content=data.get("content", ""),
            options=data.get("options", []),
            answer=data.get("answer", ""),
            question_type=data.get("question_type", "trac_nghiem"),
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

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "subject": self.subject,
            "difficulty": self.difficulty,
            "questions": [q.to_dict() for q in self.questions],
            "source_file": self.source_file,
            "created_at": self.created_at,
        }

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
        )


@dataclass
class SearchResult:
    exam: Exam
    score: float
    matched_questions: List[Question] = field(default_factory=list)
