import streamlit as st
from config import ALL_SUBJECTS, DIFFICULTIES, QUESTION_TYPES, GRADES
from frontend.utils.ui_helpers import DIFFICULTY_LABELS, QUESTION_TYPE_LABELS


def render_sidebar_filters() -> dict:
    st.sidebar.header("⚙️ Bộ lọc")

    subject_options = ["Tất cả"] + ALL_SUBJECTS
    subject_choice = st.sidebar.selectbox("Môn học", subject_options)

    # Lớp (1-12)
    grade_options = ["Tất cả"] + [f"Lớp {g}" for g in GRADES]
    grade_choice_label = st.sidebar.selectbox("Lớp", grade_options)
    grade_choice = None
    if grade_choice_label != "Tất cả":
        grade_choice = int(grade_choice_label.replace("Lớp ", ""))

    diff_options = ["Tất cả"] + [DIFFICULTY_LABELS.get(d, d) for d in DIFFICULTIES]
    diff_choice_label = st.sidebar.selectbox("Mức độ", diff_options)

    diff_choice = None
    if diff_choice_label != "Tất cả":
        matched = next((k for k, v in DIFFICULTY_LABELS.items() if v == diff_choice_label), None)
        # "Hỗn hợp" = trộn tất cả mức độ → không lọc
        diff_choice = None if matched == "hon_hop" else matched

    type_options = ["Tất cả"] + [QUESTION_TYPE_LABELS.get(t, t) for t in QUESTION_TYPES]
    type_choice_label = st.sidebar.selectbox("Loại đề", type_options)

    type_choice = None
    if type_choice_label != "Tất cả":
        type_choice = next((k for k, v in QUESTION_TYPE_LABELS.items() if v == type_choice_label), None)

    top_k = st.sidebar.slider("Số kết quả hiển thị", min_value=5, max_value=50, value=10, step=5)

    st.sidebar.divider()
    st.sidebar.subheader("🌐 Tìm trên Web")
    web_search = st.sidebar.checkbox("Tìm thêm đề thi trên Internet", value=True)

    return {
        "subject": None if subject_choice == "Tất cả" else subject_choice,
        "grade": grade_choice,
        "difficulty": diff_choice,
        "question_type": type_choice,
        "top_k": top_k,
        "web_search": web_search,
    }
