from backend.extractors.pdf_extractor import extract_from_pdf
from backend.extractors.docx_extractor import extract_from_docx
from backend.extractors.txt_extractor import extract_from_txt
from backend.schemas.exam import Question
from typing import List


def extract_from_file(file_bytes: bytes, file_name: str) -> List[Question]:
    ext = "." + file_name.rsplit(".", 1)[-1].lower() if "." in file_name else ""
    if ext == ".pdf":
        return extract_from_pdf(file_bytes)
    elif ext == ".docx":
        return extract_from_docx(file_bytes)
    elif ext == ".txt":
        return extract_from_txt(file_bytes)
    else:
        raise ValueError(f"Định dạng '{ext}' không được hỗ trợ. Chỉ hỗ trợ: .pdf, .docx, .txt")
