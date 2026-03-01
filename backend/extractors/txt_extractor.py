from typing import List

from backend.schemas.exam import Question
from backend.core.text_processor import TextProcessor


def extract_from_txt(file_bytes: bytes) -> List[Question]:
    # Thử decode UTF-8 trước, fallback sang latin-1
    try:
        text = file_bytes.decode("utf-8")
    except UnicodeDecodeError:
        text = file_bytes.decode("latin-1")

    if not text.strip():
        return []

    processor = TextProcessor()
    return processor.extract_questions(text)
