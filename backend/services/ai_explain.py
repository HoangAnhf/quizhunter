"""AI giải thích đáp án câu hỏi."""
from config import GROQ_API_KEYS, GROQ_MODEL, GROQ_ENABLED


def explain_answer(content: str, options: list, answer: str, subject: str = "", grade: int = 0) -> str:
    """Gọi Groq AI giải thích tại sao đáp án đúng. Trả '' nếu lỗi."""
    if not GROQ_ENABLED:
        return "Chưa cấu hình API key."

    from groq import Groq

    options_text = "\n".join(options) if options else "(Không có lựa chọn)"
    grade_text = f" lớp {grade}" if grade else ""

    prompt = f"""Giải thích ngắn gọn tại sao đáp án đúng cho câu hỏi sau (môn {subject}{grade_text}):

Câu hỏi: {content}
{options_text}
Đáp án đúng: {answer}

Yêu cầu:
- Giải thích bằng tiếng Việt, ngắn gọn 2-4 câu
- Nêu lý do đáp án đúng
- Nếu là trắc nghiệm, giải thích tại sao các đáp án khác sai (1 dòng mỗi đáp án sai)"""

    clients = [Groq(api_key=k) for k in GROQ_API_KEYS]
    for client in clients:
        try:
            response = client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "system", "content": "Bạn là giáo viên Việt Nam giỏi, giải thích đáp án rõ ràng và dễ hiểu."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=1024,
            )
            return response.choices[0].message.content.strip()
        except Exception:
            continue

    return "Không thể giải thích lúc này. Vui lòng thử lại."
