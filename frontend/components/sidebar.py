import streamlit as st
from config import SUBJECTS, DIFFICULTIES, QUESTION_TYPES
from frontend.utils.ui_helpers import DIFFICULTY_LABELS, QUESTION_TYPE_LABELS


def render_sidebar_filters() -> dict:
    st.sidebar.header("⚙️ Bộ lọc")

    subject_options = ["Tất cả"] + SUBJECTS
    subject_choice = st.sidebar.selectbox("Môn học", subject_options)

    diff_options = ["Tất cả"] + [DIFFICULTY_LABELS.get(d, d) for d in DIFFICULTIES]
    diff_choice_label = st.sidebar.selectbox("Mức độ", diff_options)

    diff_choice = None
    if diff_choice_label != "Tất cả":
        diff_choice = next((k for k, v in DIFFICULTY_LABELS.items() if v == diff_choice_label), None)

    type_options = ["Tất cả"] + [QUESTION_TYPE_LABELS.get(t, t) for t in QUESTION_TYPES]
    type_choice_label = st.sidebar.selectbox("Loại đề", type_options)

    type_choice = None
    if type_choice_label != "Tất cả":
        type_choice = next((k for k, v in QUESTION_TYPE_LABELS.items() if v == type_choice_label), None)

    top_k = st.sidebar.slider("Số kết quả hiển thị", min_value=5, max_value=50, value=10, step=5)

    return {
        "subject": None if subject_choice == "Tất cả" else subject_choice,
        "difficulty": diff_choice,
        "question_type": type_choice,
        "top_k": top_k
    }