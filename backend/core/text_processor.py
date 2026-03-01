import re
import uuid
from typing import List

from backend.schemas.exam import Question


class TextProcessor:
    """Trích xuất câu hỏi từ văn bản thuần (raw text)."""

    # Patterns nhận diện câu hỏi
    QUESTION_PATTERNS = [
        # Câu 1: ..., Câu 2. ..., Question 1: ...
        r'(?:Câu|Question|Cau)\s*(\d+)\s*[.:)]\s*(.*?)(?=(?:Câu|Question|Cau)\s*\d+\s*[.:)]|$)',
        # 1. ..., 2. ..., 1) ...
        r'(?:^|\n)\s*(\d+)\s*[.)]\s*(.*?)(?=\n\s*\d+\s*[.)]|$)',
    ]

    OPTION_PATTERN = re.compile(
        r'^\s*([A-Ea-e])\s*[.):\-]\s*(.+)', re.MULTILINE
    )

    ANSWER_PATTERNS = [
        # Đáp án: A, Answer: B
        re.compile(r'(?:Đáp án|Dap an|Answer|Correct)\s*[.:]\s*([A-Ea-e])', re.IGNORECASE),
        # A ✓, A ✔, A (đúng), A (correct)
        re.compile(r'([A-Ea-e])\s*[✓✔]', re.IGNORECASE),
        re.compile(r'([A-Ea-e])\s*\(\s*(?:đúng|correct|right)\s*\)', re.IGNORECASE),
    ]

    def extract_questions(self, raw_text: str) -> List[Question]:
        if not raw_text or not raw_text.strip():
            return []

        # Thử tách theo pattern câu hỏi có đánh số
        questions = self._extract_numbered_questions(raw_text)

        if not questions:
            # Fallback: tách theo dòng trống
            questions = self._extract_by_blank_lines(raw_text)

        return questions

    def _extract_numbered_questions(self, text: str) -> List[Question]:
        questions = []

        # Tách theo pattern "Câu X:" hoặc "X."
        parts = re.split(r'(?:Câu|Question|Cau)\s*\d+\s*[.:)]', text, flags=re.IGNORECASE)
        headers = re.findall(r'(?:Câu|Question|Cau)\s*(\d+)\s*[.:)]', text, flags=re.IGNORECASE)

        if len(headers) == 0:
            # Thử pattern số đơn giản: 1. hoặc 1)
            parts = re.split(r'\n\s*\d+\s*[.)]', text)
            headers = re.findall(r'\n\s*(\d+)\s*[.)]', text)
            if parts and len(parts) > len(headers):
                parts = parts[1:]  # bỏ phần trước câu 1

        if len(headers) == 0:
            return []

        for i, (num, part) in enumerate(zip(headers, parts)):
            part = part.strip()
            if not part:
                continue

            lines = part.split('\n')
            content_lines = []
            options = []
            answer = ""

            for line in lines:
                line_stripped = line.strip()
                if not line_stripped:
                    continue

                opt_match = self.OPTION_PATTERN.match(line_stripped)
                if opt_match:
                    opt_letter = opt_match.group(1).upper()
                    opt_text = opt_match.group(2).strip()
                    options.append(f"{opt_letter}. {opt_text}")
                else:
                    # Kiểm tra đáp án
                    ans_found = False
                    for pat in self.ANSWER_PATTERNS:
                        m = pat.search(line_stripped)
                        if m:
                            answer = m.group(1).upper()
                            ans_found = True
                            break
                    if not ans_found:
                        content_lines.append(line_stripped)

            content = ' '.join(content_lines).strip()
            if not content:
                continue

            q_type = "trac_nghiem" if options else "tu_luan"

            questions.append(Question(
                id=str(uuid.uuid4()),
                content=content,
                options=options,
                answer=answer,
                question_type=q_type,
            ))

        return questions

    def _extract_by_blank_lines(self, text: str) -> List[Question]:
        blocks = re.split(r'\n\s*\n', text.strip())
        questions = []

        for block in blocks:
            block = block.strip()
            if not block or len(block) < 10:
                continue

            lines = block.split('\n')
            content_lines = []
            options = []
            answer = ""

            for line in lines:
                line_stripped = line.strip()
                if not line_stripped:
                    continue

                opt_match = self.OPTION_PATTERN.match(line_stripped)
                if opt_match:
                    opt_letter = opt_match.group(1).upper()
                    opt_text = opt_match.group(2).strip()
                    options.append(f"{opt_letter}. {opt_text}")
                else:
                    for pat in self.ANSWER_PATTERNS:
                        m = pat.search(line_stripped)
                        if m:
                            answer = m.group(1).upper()
                            break
                    else:
                        content_lines.append(line_stripped)

            content = ' '.join(content_lines).strip()
            if not content:
                continue

            q_type = "trac_nghiem" if options else "tu_luan"

            questions.append(Question(
                id=str(uuid.uuid4()),
                content=content,
                options=options,
                answer=answer,
                question_type=q_type,
            ))

        return questions
