from typing import List

from backend.schemas.exam import Question
from backend.models.classification_model import ClassificationModel


class ExamClassifier:
    """Phân loại tự động đề thi theo môn học, mức độ, loại câu hỏi."""

    def __init__(self):
        self.model = ClassificationModel()

    def classify(self, questions: List[Question]) -> dict:
        # Gộp toàn bộ nội dung câu hỏi thành 1 chuỗi để phân tích
        all_text = " ".join(q.content for q in questions)
        all_text += " " + " ".join(
            " ".join(q.options) for q in questions if q.options
        )

        subject, sub_conf = self.model.predict_subject(all_text)
        difficulty, diff_conf = self.model.predict_difficulty(all_text)
        question_type = self.model.predict_question_type(questions)

        avg_confidence = (sub_conf + diff_conf) / 2

        return {
            "subject": subject,
            "difficulty": difficulty,
            "question_type": question_type,
            "confidence": round(avg_confidence, 2),
        }
