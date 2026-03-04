import streamlit as st
from pathlib import Path
from datetime import datetime

DIFFICULTY_LABELS = {
    "co_ban": "Cơ bản",
    "trung_binh": "Trung bình",
    "nang_cao": "Nâng cao",
    "hon_hop": "Hỗn hợp",
}

QUESTION_TYPE_LABELS = {
    "trac_nghiem": "Trắc nghiệm",
    "tu_luan": "Tự luận",
    "bai_tap": "Bài tập",
    "noi_cot": "Nối cột",
}

def load_css():
    css_path = Path(__file__).parent.parent / "static" / "style.css"
    if css_path.exists():
        with open(css_path, encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def difficulty_badge(difficulty: str) -> str:
    label = DIFFICULTY_LABELS.get(difficulty, difficulty)
    return f'<span class="badge badge-{difficulty}">{label}</span>'

def subject_badge(subject: str) -> str:
    return f'<span class="badge badge-subject">{subject}</span>'

def question_type_badge(q_type: str) -> str:
    label = QUESTION_TYPE_LABELS.get(q_type, q_type)
    return f'<span class="badge badge-type">{label}</span>'

def format_score(score: float) -> str:
    return f"{int(score * 100)}%"

def format_datetime(iso_string: str) -> str:
    try:
        dt = datetime.fromisoformat(iso_string.replace('Z', '+00:00'))
        return dt.strftime('%d/%m/%Y %H:%M')
    except Exception:
        return iso_string

def truncate_text(text: str, max_length: int = 100) -> str:
    if len(text) > max_length:
        return text[:max_length] + "..."
    return text