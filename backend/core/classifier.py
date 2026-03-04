from typing import List, Optional

from backend.schemas.exam import Question
from backend.models.classification_model import ClassificationModel


class ExamClassifier:
    """Phân loại tự động đề thi theo môn học, mức độ, loại câu hỏi."""

    def __init__(self):
        self.model = ClassificationModel()

    def classify(self, questions: List[Question]) -> dict:
        """Phân loại đề thi dựa trên nội dung câu hỏi."""
        # Gộp toàn bộ nội dung câu hỏi thành 1 chuỗi để phân tích
        all_text = " ".join(q.content for q in questions)
        all_text += " " + " ".join(
            " ".join(q.options) for q in questions if q.options
        )
        # Thêm answers vào context
        all_text += " " + " ".join(
            q.answer for q in questions if q.answer
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

    def classify_with_audio(self, audio_bytes: bytes, questions: List[Question]) -> dict:
        """Phân loại kết hợp keyword classifier + Deepgram audio analysis."""
        # Classifier keyword trước
        base_result = self.classify(questions)

        try:
            from backend.services.deepgram_service import DeepgramService
            svc = DeepgramService()
            if svc.is_available():
                audio_result = svc.transcribe_with_details(audio_bytes)
                transcript = audio_result.get("transcript", "")

                if transcript:
                    # Phân loại transcript để bổ sung context
                    all_text = transcript + " " + " ".join(q.content for q in questions)
                    subject, sub_conf = self.model.predict_subject(all_text)
                    difficulty, diff_conf = self.model.predict_difficulty(all_text)

                    # Nếu Deepgram cho confidence cao hơn, dùng kết quả đó
                    if sub_conf > base_result["confidence"]:
                        base_result["subject"] = subject
                    if diff_conf > base_result["confidence"]:
                        base_result["difficulty"] = difficulty

                    # Cập nhật confidence
                    new_conf = (sub_conf + diff_conf) / 2
                    base_result["confidence"] = round(
                        max(base_result["confidence"], new_conf), 2
                    )
        except Exception:
            pass

        return base_result
