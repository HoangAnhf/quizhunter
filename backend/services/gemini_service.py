"""Gemini AI — sinh câu hỏi khi ngân hàng không đủ."""
import json
import uuid
from typing import List, Optional

import google.generativeai as genai

from backend.schemas.exam import Question
from backend.services.curriculum import get_curriculum_hint
from config import GEMINI_API_KEY

genai.configure(api_key=GEMINI_API_KEY)
_model = genai.GenerativeModel("gemini-2.0-flash")


def generate_questions(
    subject: str,
    grade: int,
    topic: Optional[str] = None,
    difficulty: str = "trung_binh",
    num_questions: int = 10,
    question_type: str = "trac_nghiem",
) -> List[Question]:
    """Sinh câu hỏi tiếng Việt qua Gemini API. Trả [] nếu lỗi."""
    difficulty_vi = {
        "co_ban": "cơ bản, dễ",
        "trung_binh": "trung bình",
        "nang_cao": "nâng cao, khó",
    }.get(difficulty, "trung bình")

    type_instruction = {
        "trac_nghiem": "Mỗi câu có 4 lựa chọn A, B, C, D. Chỉ có 1 đáp án đúng.",
        "tu_luan": "Câu hỏi tự luận, đáp án là đáp số hoặc lời giải ngắn.",
        "bai_tap": "Bài tập yêu cầu tính toán hoặc giải thích.",
    }.get(question_type, "Câu trắc nghiệm 4 lựa chọn.")

    topic_text = f"\nChủ đề cụ thể: {topic}" if topic else ""
    curriculum = get_curriculum_hint(subject, grade)
    curriculum_text = f"\n\nCHƯƠNG TRÌNH LỚP {grade} GỒM: {curriculum}" if curriculum else ""

    prompt = f"""Bạn là giáo viên {subject} lớp {grade} tại Việt Nam. Hãy tạo {num_questions} câu hỏi kiểm tra.

Môn: {subject}
Lớp: {grade}
Mức độ: {difficulty_vi}
Dạng: {type_instruction}{topic_text}{curriculum_text}

YÊU CẦU BẮT BUỘC:
- Câu hỏi PHẢI đúng chương trình SGK lớp {grade} Việt Nam
- TUYỆT ĐỐI KHÔNG được ra câu hỏi thuộc chương trình lớp khác
- Nội dung phải phù hợp với độ tuổi và kiến thức học sinh lớp {grade}
- Nếu mức độ "cơ bản" thì ra câu dễ nhưng vẫn đúng kiến thức lớp {grade}
- Nếu mức độ "nâng cao" thì ra câu khó hơn nhưng vẫn trong phạm vi lớp {grade}, KHÔNG vượt cấp

Trả về JSON array, mỗi phần tử có format:
{{
  "content": "Nội dung câu hỏi",
  "options": ["A. ...", "B. ...", "C. ...", "D. ..."],
  "answer": "B",
  "question_type": "{question_type}",
  "topic": "Tên chủ đề trong chương trình lớp {grade}"
}}

Nếu là tu_luan hoặc bai_tap thì options = [] và answer là đáp số.
CHỈ trả về JSON array, không giải thích thêm."""

    try:
        response = _model.generate_content(prompt)
        text = response.text.strip()

        # Strip markdown code fences
        if text.startswith("```"):
            text = text.split("\n", 1)[1]
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0]
        text = text.strip()

        data = json.loads(text)
        questions = []
        for item in data:
            q = Question(
                id=f"gemini-{uuid.uuid4().hex[:8]}",
                content=item.get("content", ""),
                options=item.get("options", []),
                answer=item.get("answer", ""),
                question_type=item.get("question_type", question_type),
                grade=grade,
                topic=item.get("topic", topic),
            )
            questions.append(q)
        return questions

    except Exception:
        return []
