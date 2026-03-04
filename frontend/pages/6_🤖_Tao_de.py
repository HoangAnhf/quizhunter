import uuid
from datetime import datetime, timezone

import streamlit as st
import sys
from pathlib import Path

root_path = Path(__file__).parent.parent.parent
if str(root_path) not in sys.path:
    sys.path.append(str(root_path))

from frontend.utils.ui_helpers import load_css, DIFFICULTY_LABELS, QUESTION_TYPE_LABELS
from config import VI_SUBJECTS, GRADES, DIFFICULTIES, GROQ_ENABLED, GEMINI_ENABLED

st.set_page_config(page_title="Tạo Đề Tự Động", page_icon="🤖", layout="wide")
load_css()

st.title("🤖 Tạo Đề Tự Động bằng AI")
st.caption("Chọn môn học, lớp, số câu → AI sẽ tạo đề thi hoàn chỉnh cho bạn.")

if not GROQ_ENABLED and not GEMINI_ENABLED:
    st.error("Chưa cấu hình API key cho Groq hoặc Gemini. Vui lòng thêm vào config.py.")
    st.stop()

# --- Form tạo đề ---
with st.form("create_exam_form"):
    col1, col2 = st.columns(2)
    with col1:
        subject = st.selectbox("📘 Môn học", VI_SUBJECTS)
        grade = st.selectbox("🎓 Lớp", GRADES, index=7)  # default lớp 8
        num_questions = st.slider("📝 Số câu hỏi", min_value=5, max_value=40, value=25, step=5)

    with col2:
        diff_label = st.selectbox("📊 Mức độ", [DIFFICULTY_LABELS[d] for d in DIFFICULTIES])
        difficulty = next(k for k, v in DIFFICULTY_LABELS.items() if v == diff_label)
        q_type_label = st.selectbox("📋 Dạng câu hỏi", ["Trắc nghiệm", "Tự luận", "Bài tập", "Hỗn hợp"])
        topic = st.text_input("🏷️ Chủ đề (tùy chọn)", placeholder="VD: phương trình bậc hai, quang hợp...")

    submitted = st.form_submit_button("🚀 Tạo đề ngay", use_container_width=True, type="primary")

if submitted:
    q_type_map = {"Trắc nghiệm": "trac_nghiem", "Tự luận": "tu_luan", "Bài tập": "bai_tap", "Hỗn hợp": "trac_nghiem"}
    question_type = q_type_map[q_type_label]

    # Hỗn hợp mức độ: chia đều 3 mức
    if difficulty == "hon_hop":
        diff_list = [
            ("co_ban", num_questions // 3),
            ("trung_binh", num_questions // 3),
            ("nang_cao", num_questions - 2 * (num_questions // 3)),
        ]
    else:
        diff_list = [(difficulty, num_questions)]

    with st.spinner(f"Đang tạo {num_questions} câu {subject} lớp {grade}..."):
        questions = []
        last_error = ""
        ai_source = ""

        for diff_item, n_qs in diff_list:
            batch = []

            if GROQ_ENABLED and not batch:
                try:
                    from backend.services.groq_service import generate_questions as groq_gen
                    batch = groq_gen(
                        subject=subject, grade=grade,
                        topic=topic if topic else None,
                        difficulty=diff_item,
                        num_questions=n_qs,
                        question_type=question_type,
                    )
                    ai_source = "Groq AI (Llama 3.3)"
                except Exception as e:
                    last_error = f"Groq: {e}"

            if not batch and GEMINI_ENABLED:
                try:
                    from backend.services.gemini_service import generate_questions as gemini_gen
                    batch = gemini_gen(
                        subject=subject, grade=grade,
                        topic=topic if topic else None,
                        difficulty=diff_item,
                        num_questions=n_qs,
                        question_type=question_type,
                    )
                    ai_source = "Google Gemini AI"
                except Exception as e:
                    last_error += f" | Gemini: {e}"

            questions.extend(batch)

    if not questions:
        st.error(f"AI không thể tạo đề lúc này. Lỗi: {last_error}")
    else:
        st.toast(f"Đã tạo {len(questions)} câu hỏi!", icon="✅")

        # Lưu vào session để hiển thị
        st.session_state["generated_exam"] = {
            "questions": questions,
            "subject": subject,
            "grade": grade,
            "difficulty": difficulty,
            "ai_source": ai_source,
            "topic": topic,
        }

# --- Hiển thị đề đã tạo ---
if "generated_exam" in st.session_state:
    data = st.session_state["generated_exam"]
    questions = data["questions"]

    st.write("---")
    st.subheader(f"📄 {data['subject']} - Lớp {data['grade']} ({len(questions)} câu)")
    st.caption(f"Mức độ: {DIFFICULTY_LABELS.get(data['difficulty'], data['difficulty'])} | Nguồn: {data['ai_source']}")
    if data.get("topic"):
        st.caption(f"Chủ đề: {data['topic']}")

    for j, q in enumerate(questions, 1):
        type_label = QUESTION_TYPE_LABELS.get(q.question_type, "")
        if type_label:
            type_label = f" ({type_label})"

        st.markdown(f"**Câu {j}{type_label}:** {q.content}")
        if q.options:
            for opt in q.options:
                st.markdown(f"&emsp;{opt}")

        if q.answer:
            ans_col, exp_col = st.columns(2)
            with ans_col:
                with st.popover(f"Đáp án câu {j}"):
                    st.markdown(f"**{q.answer}**")
            with exp_col:
                if st.button("💡 Giải thích", key=f"explain_gen_{j}"):
                    with st.spinner("AI đang giải thích..."):
                        from backend.services.ai_explain import explain_answer
                        explanation = explain_answer(
                            content=q.content,
                            options=q.options or [],
                            answer=q.answer,
                            subject=data["subject"],
                            grade=data.get("grade", 0),
                        )
                    st.info(explanation)
        st.divider()

    # Nút hành động
    col_save, col_quiz, col_new = st.columns(3)
    with col_quiz:
        if st.button("📝 Làm đề ngay", use_container_width=True):
            # Luu tam roi chuyen sang trang lam de
            try:
                from backend.database.mysql_store import MySQLExamStore
                from backend.schemas.exam import Exam

                _store = MySQLExamStore()
                grade_text = f" - Lớp {data['grade']}" if data['grade'] else ""
                topic_text = f" - {data['topic']}" if data.get('topic') else ""
                _exam = Exam(
                    id=str(uuid.uuid4()),
                    title=f"{data['subject']}{grade_text}{topic_text} ({len(questions)} câu)",
                    subject=data["subject"],
                    difficulty=data["difficulty"],
                    questions=questions,
                    source_file=data["ai_source"],
                    created_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                    grade=data["grade"],
                )
                _exam_id = _store.save(exam=_exam)
                st.session_state.start_quiz_exam_id = _exam_id
                st.switch_page("pages/8_📝_Lam_de.py")
            except Exception as e:
                st.error(f"Lỗi: {e}")
    with col_save:
        if st.button("💾 Lưu vào Kho đề", use_container_width=True, type="primary"):
            try:
                from backend.database.mysql_store import MySQLExamStore
                from backend.schemas.exam import Exam

                store = MySQLExamStore()
                grade_text = f" - Lớp {data['grade']}" if data['grade'] else ""
                topic_text = f" - {data['topic']}" if data.get('topic') else ""
                exam = Exam(
                    id=str(uuid.uuid4()),
                    title=f"{data['subject']}{grade_text}{topic_text} ({len(questions)} câu)",
                    subject=data["subject"],
                    difficulty=data["difficulty"],
                    questions=questions,
                    source_file=data["ai_source"],
                    created_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                    grade=data["grade"],
                )
                exam_id = store.save(exam=exam)
                st.success(f"Đã lưu vào kho đề! (ID: {exam_id})")
            except Exception as e:
                st.error(f"Lỗi khi lưu: {e}")

    with col_new:
        if st.button("🔄 Tạo đề mới", use_container_width=True):
            if "generated_exam" in st.session_state:
                del st.session_state["generated_exam"]
            st.rerun()
