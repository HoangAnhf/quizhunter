import uuid
from datetime import datetime

import streamlit as st
import sys
from pathlib import Path

root_path = Path(__file__).parent.parent.parent
if str(root_path) not in sys.path:
    sys.path.append(str(root_path))

from frontend.utils.ui_helpers import load_css, DIFFICULTY_LABELS, QUESTION_TYPE_LABELS
from frontend.components.search_bar import render_search_bar
from frontend.components.sidebar import render_sidebar_filters
from frontend.components.exam_card import render_exam_card

st.set_page_config(page_title="Tìm kiếm Đề Thi", page_icon="🔍", layout="wide")
load_css()


@st.cache_resource(show_spinner=False)
def get_search_engine():
    from backend.core.search_engine import SearchEngine
    return SearchEngine()

if "search_query" not in st.session_state:
    st.session_state.search_query = ""
if "voice_text" not in st.session_state:
    st.session_state.voice_text = ""

filters = render_sidebar_filters()

st.title("🔍 Tìm kiếm Đề Thi")

# Voice Search
with st.expander("🎤 Tìm kiếm bằng giọng nói", expanded=False):
    st.caption("Bấm nút → nói nội dung cần tìm → bấm lại để dừng. Hỗ trợ tiếng Việt và tiếng Anh.")
    try:
        from streamlit_mic_recorder import speech_to_text

        text = speech_to_text(
            start_prompt="🎤 Bấm để ghi âm",
            stop_prompt="⏹️ Bấm để dừng",
            just_once=False,
            use_container_width=True,
            language="vi-VN",
            key="voice_search",
        )

        if text:
            st.success(f'✅ Nhận dạng được: "{text}"')
            st.session_state.voice_text = text
            st.session_state.search_query = text
    except ImportError:
        st.warning("Cần cài đặt: `pip install streamlit-mic-recorder`")

# Search Interface
query = render_search_bar(placeholder="Nhập nội dung đề thi, khái niệm, câu hỏi...")

# Lịch sử tìm kiếm gần đây
try:
    from backend.database.mysql_store import MySQLExamStore as _Store
    _recent = _Store().get_recent_searches(8)
    if _recent:
        st.caption("Tìm gần đây:")
        _cols = st.columns(min(len(_recent), 4))
        for _i, _kw in enumerate(_recent):
            with _cols[_i % min(len(_recent), 4)]:
                if st.button(_kw, key=f"hist_{_i}", use_container_width=True):
                    st.session_state.search_query = _kw
                    st.rerun()
except Exception:
    pass

# Khi form submit query mới → cập nhật session state
if query:
    st.session_state.search_query = query
    st.session_state.voice_text = ""
elif st.session_state.voice_text:
    st.session_state.search_query = st.session_state.voice_text
    st.session_state.voice_text = ""

active_query = st.session_state.search_query

if active_query:

    # === Tab kết quả: Kho đề + Web ===
    tab_local, tab_web = st.tabs(["📚 Kho đề (Local)", "🌐 Tìm trên Web"])

    # --- Tab 1: Kho đề local ---
    with tab_local:
        with st.spinner("AI đang phân tích và tìm kiếm ngữ nghĩa..."):
            try:
                search_engine = get_search_engine()
                results = search_engine.search(
                    query=active_query,
                    subject=filters["subject"],
                    difficulty=filters["difficulty"],
                    question_type=filters["question_type"],
                    grade=filters.get("grade"),
                    top_k=filters["top_k"],
                )

                if not results:
                    st.warning(
                        "Không tìm thấy đề thi phù hợp trong kho đề. Thử tìm trên tab **🌐 Tìm trên Web**."
                    )
                else:
                    st.success(f"Tìm thấy {len(results)} kết quả phù hợp nhất trong kho đề.")
                    for i, res in enumerate(results):
                        render_exam_card(res, i)
                        # Nút làm đề ngay
                        if st.button("📝 Làm đề ngay", key=f"quiz_local_{i}", use_container_width=False):
                            st.session_state.start_quiz_exam_id = res.exam.id
                            st.switch_page("pages/8_📝_Lam_de.py")
            except Exception as e:
                st.error(f"Đã xảy ra lỗi khi tìm kiếm: {e}")

    # --- Tab 2: Tìm trên Web ---
    with tab_web:
        if not filters.get("web_search", True):
            st.info("Tìm kiếm trên web đang tắt. Bật lại ở thanh bên trái.")
        else:
            with st.spinner("🌐 Đang tìm đề thi trên Internet và dịch sang tiếng Việt... (15-20 giây)"):
                try:
                    from backend.services.web_search import WebSearchService

                    web_service = WebSearchService()
                    web_results = web_service.search_web(
                        query=active_query,
                        subject=filters["subject"],
                        difficulty=filters["difficulty"],
                        grade=filters.get("grade"),
                    )

                    if not web_results:
                        st.warning(
                            "Không tìm thấy đề thi phù hợp trên web. Thử thay đổi từ khóa."
                        )
                    else:
                        st.success(f"Tìm thấy đề thi từ {len(web_results)} trang web.")

                        for i, res in enumerate(web_results):
                            exam = res.exam
                            q_count = len(exam.questions)

                            with st.container():
                                st.markdown(f"### 🌐 {exam.title}")
                                col_info, col_action = st.columns([3, 1])

                                with col_info:
                                    st.caption(f"Nguồn: {exam.source_file}")
                                    st.markdown(
                                        f"**{q_count} câu hỏi** | "
                                        f"Môn: {exam.subject} | "
                                        f"Mức độ: {DIFFICULTY_LABELS.get(exam.difficulty, exam.difficulty)}"
                                    )

                                with col_action:
                                    if st.button(
                                        "💾 Lưu vào Kho đề",
                                        key=f"save_web_{i}",
                                        use_container_width=True,
                                    ):
                                        try:
                                            from backend.database.mysql_store import MySQLExamStore
                                            from backend.schemas.exam import Exam

                                            store = MySQLExamStore()
                                            save_exam = Exam(
                                                id=str(uuid.uuid4()),
                                                title=exam.title,
                                                subject=exam.subject,
                                                difficulty=exam.difficulty,
                                                questions=exam.questions,
                                                source_file=exam.source_file,
                                                created_at=datetime.utcnow().isoformat() + "Z",
                                            )
                                            exam_id = store.save(exam=save_exam)
                                            st.success(f"Đã lưu! (ID: {exam_id})")
                                            st.session_state[f"saved_web_{i}"] = exam_id
                                        except Exception as e:
                                            st.error(f"Lỗi khi lưu: {e}")

                                    # Nút làm đề ngay (lưu trước rồi chuyển)
                                    if st.button(
                                        "📝 Làm đề ngay",
                                        key=f"quiz_web_{i}",
                                        use_container_width=True,
                                    ):
                                        try:
                                            from backend.database.mysql_store import MySQLExamStore
                                            from backend.schemas.exam import Exam

                                            store = MySQLExamStore()
                                            # Kiểm tra đã lưu chưa
                                            saved_id = st.session_state.get(f"saved_web_{i}")
                                            if not saved_id:
                                                save_exam = Exam(
                                                    id=str(uuid.uuid4()),
                                                    title=exam.title,
                                                    subject=exam.subject,
                                                    difficulty=exam.difficulty,
                                                    questions=exam.questions,
                                                    source_file=exam.source_file,
                                                    created_at=datetime.utcnow().isoformat() + "Z",
                                                )
                                                saved_id = store.save(exam=save_exam)
                                            st.session_state.start_quiz_exam_id = saved_id
                                            st.switch_page("pages/8_📝_Lam_de.py")
                                        except Exception as e:
                                            st.error(f"Lỗi: {e}")

                                # Hiển thị câu hỏi trích xuất
                                with st.expander(f"👁️ Xem {q_count} câu hỏi", expanded=False):
                                    for j, q in enumerate(exam.questions, 1):
                                        # Label theo dạng câu hỏi
                                        type_label = ""
                                        if q.question_type == "tu_luan":
                                            type_label = " (Tự luận)"
                                        elif q.question_type == "noi_cot":
                                            type_label = " (Nối cột)"
                                        st.markdown(f"**Câu {j}{type_label}:** {q.content}")

                                        # Nối cột: hiện bảng 2 cột
                                        if q.question_type == "noi_cot" and q.column_a and q.column_b:
                                            rows = ""
                                            for k in range(max(len(q.column_a), len(q.column_b))):
                                                left = f"{k+1}. {q.column_a[k]}" if k < len(q.column_a) else ""
                                                right = f"{chr(97+k)}. {q.column_b[k]}" if k < len(q.column_b) else ""
                                                rows += f"<tr><td style='padding:6px 12px;border:1px solid #ddd;'>{left}</td><td style='padding:6px 12px;border:1px solid #ddd;'>{right}</td></tr>"
                                            st.markdown(f"""
                                            <table style="width:100%;border-collapse:collapse;margin:8px 0;">
                                                <tr>
                                                    <th style="padding:6px 12px;border:1px solid #ddd;background:#f0f2f6;text-align:left;width:50%;">Cột A</th>
                                                    <th style="padding:6px 12px;border:1px solid #ddd;background:#f0f2f6;text-align:left;width:50%;">Cột B</th>
                                                </tr>
                                                {rows}
                                            </table>
                                            """, unsafe_allow_html=True)
                                        elif q.options:
                                            for opt in q.options:
                                                st.markdown(f"- {opt}")

                                        if q.answer:
                                            ans_col, exp_col = st.columns(2)
                                            with ans_col:
                                                with st.popover("Xem đáp án"):
                                                    st.markdown(f"**Đáp án: {q.answer}**")
                                            with exp_col:
                                                if st.button("💡 Giải thích", key=f"explain_{i}_{j}"):
                                                    with st.spinner("AI đang giải thích..."):
                                                        from backend.services.ai_explain import explain_answer
                                                        explanation = explain_answer(
                                                            content=q.content,
                                                            options=q.options or [],
                                                            answer=q.answer,
                                                            subject=exam.subject,
                                                            grade=exam.grade or 0,
                                                        )
                                                    st.info(explanation)
                                        st.divider()

                                st.divider()

                except Exception as e:
                    st.error(f"Đã xảy ra lỗi khi tìm trên web: {e}")
else:
    st.info(
        "Nhập từ khóa vào thanh tìm kiếm hoặc dùng 🎤 giọng nói để bắt đầu."
    )
