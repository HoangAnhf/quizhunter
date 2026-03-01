import io
from typing import List

from backend.schemas.exam import Question
from backend.core.text_processor import TextProcessor


def extract_from_pdf(file_bytes: bytes) -> List[Question]:
    try:
        import PyPDF2
    except ImportError:
        raise ImportError("Cần cài đặt PyPDF2: pip install PyPDF2")

    reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
    full_text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            full_text += page_text + "\n"

    if not full_text.strip():
        return []

    processor = TextProcessor()
    return processor.extract_questions(full_text)
