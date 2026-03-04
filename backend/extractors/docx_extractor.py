import io
from typing import List
import docx

from backend.schemas.exam import Question
from backend.core.text_processor import TextProcessor


def extract_from_docx(file_bytes: bytes) -> List[Question]:
    doc = docx.Document(io.BytesIO(file_bytes))
    full_text = "\n".join(para.text for para in doc.paragraphs if para.text.strip())

    if not full_text.strip():
        return []

    processor = TextProcessor()
    return processor.extract_questions(full_text)
