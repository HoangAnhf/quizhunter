import streamlit as st
import sys
from pathlib import Path

root_path = Path(__file__).parent.parent.parent
if str(root_path) not in sys.path:
    sys.path.append(str(root_path))

from frontend.utils.ui_helpers import load_css, format_datetime, DIFFICULTY_LABELS
from frontend.components.exam_card import render_exam_detail
from config import VI_SUBJECTS, DIFFICULTIES, GRADES

st.set_page_config(page_title="Kho Đề Thi", page_icon="📚", layout="wide")
load_css()

st.title("📚 Kho Đề Thi")


@st.cache_resource(show_spinner=False)
def _get_store():
    from backend.database.mysql_store import MySQLExamStore
    return MySQLExamStore()


store = _get_store()

# Auto-backfill mã đề cho đề cũ (chạy 1 lần duy nhất)
if "exam_codes_backfilled" not in st.session_state:
    try:
        updated = store.backfill_exam_codes()
        if updated > 0:
            st.toast(f"Đã tạo mã đề cho {updated} đề thi cũ.")
    except Exception:
        pass
    st.session_state.exam_codes_backfilled = True

try:
    stats = store.get_stats()
except Exception:
    stats = {"total_exams": 0, "total_questions": 0, "subjects": {}, "difficulties": {}}

# Metrics
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f'<div class="metric-card"><h4>Tổng số đề</h4><h2>{stats.get("total_exams", 0)}</h2></div>', unsafe_allow_html=True)
with c2:
    st.markdown(f'<div class="metric-card"><h4>Tổng câu hỏi</h4><h2>{stats.get("total_questions", 0)}</h2></div>', unsafe_allow_html=True)
with c3:
    st.markdown(f'<div class="metric-card"><h4>Số môn học</h4><h2>{len(stats.get("subjects", {}))}</h2></div>', unsafe_allow_html=True)
with c4:
    diffs = stats.get("difficulties", {})
    most_common_diff = DIFFICULTY_LABELS.get(max(diffs, key=diffs.get), "N/A") if diffs else "N/A"
    st.markdown(f'<div class="metric-card"><h4>Mức độ phổ biến</h4><h2>{most_common_diff}</h2></div>', unsafe_allow_html=True)

st.write("---")

# Filters
f_col1, f_col2, f_col3 = st.columns([2, 2, 1])
with f_col1:
    filter_subject = st.selectbox("Lọc Môn học", ["Tất cả"] + VI_SUBJECTS)
with f_col2:
    filter_diff_label = st.selectbox("Lọc Mức độ", ["Tất cả"] + [DIFFICULTY_LABELS.get(d, d) for d in DIFFICULTIES])
with f_col3:
    filter_grade = st.selectbox("Lọc Lớp", ["Tất cả"] + [f"Lớp {g}" for g in GRADES])

f_sub = None if filter_subject == "Tất cả" else filter_subject
_matched_diff = next((k for k, v in DIFFICULTY_LABELS.items() if v == filter_diff_label), None) if filter_diff_label != "Tất cả" else None
f_diff = None if _matched_diff == "hon_hop" else _matched_diff
f_grade = int(filter_grade.replace("Lớp ", "")) if filter_grade != "Tất cả" else None

# Tra đề — tìm theo mã đề hoặc tên đề
search_query = st.text_input(
    "🔍 Tra đề",
    placeholder="Nhập mã đề (VD: TOAN-8-CB) hoặc tên đề thi...",
    key="exam_search_query",
)

# Pagination state
if "current_page" not in st.session_state:
    st.session_state.current_page = 1
if "prev_search_query" not in st.session_state:
    st.session_state.prev_search_query = ""

# Reset page khi search query thay đổi
if search_query != st.session_state.prev_search_query:
    st.session_state.current_page = 1
    st.session_state.prev_search_query = search_query

per_page = 10

# Data Fetching
try:
    if search_query and search_query.strip():
        exams, total_count = store.search_by_code_or_title(
            query=search_query.strip(),
            subject=f_sub, difficulty=f_diff, grade=f_grade,
            page=st.session_state.current_page, per_page=per_page,
        )
    else:
        exams = store.get_all(subject=f_sub, difficulty=f_diff, grade=f_grade, page=st.session_state.current_page, per_page=per_page)
        total_count = store.count(subject=f_sub, difficulty=f_diff, grade=f_grade)
except Exception as e:
    st.error(f"Lỗi khi tải dữ liệu: {e}")
    exams, total_count = [], 0

# Dialog Detail
@st.dialog("Chi tiết Đề Thi", width="large")
def show_exam_detail(exam_id):
    exam = store.get_by_id(exam_id=exam_id)
    if exam:
        render_exam_detail(exam)
    else:
        st.error("Không tìm thấy đề thi.")
    if st.button("Đóng", use_container_width=True):
        st.rerun()

# Data Table
if not exams:
    st.info("Không có đề thi nào phù hợp trong kho.")
else:
    col_stt, col_code, col_name, col_sub, col_diff, col_q, col_date, col_acts = st.columns([0.5, 1.5, 2.5, 1.2, 1.2, 0.8, 1.3, 1.5])
    col_stt.write("**STT**")
    col_code.write("**Mã đề**")
    col_name.write("**Tên đề thi**")
    col_sub.write("**Môn học**")
    col_diff.write("**Mức độ**")
    col_q.write("**Số câu**")
    col_date.write("**Ngày tạo**")
    col_acts.write("**Hành động**")
    st.divider()

    for idx, exam in enumerate(exams, 1):
        col_stt, col_code, col_name, col_sub, col_diff, col_q, col_date, col_acts = st.columns([0.5, 1.5, 2.5, 1.2, 1.2, 0.8, 1.3, 1.5])
        col_stt.write(f"{(st.session_state.current_page - 1) * per_page + idx}")
        col_code.write(f"`{exam.exam_code or '---'}`")
        col_name.write(f"**{exam.title}**")
        col_sub.write(exam.subject)
        col_diff.write(DIFFICULTY_LABELS.get(exam.difficulty, exam.difficulty))
        col_q.write(len(exam.questions))
        col_date.write(format_datetime(exam.created_at))
        with col_acts:
            a1, a2, a3 = st.columns(3)
            with a1:
                if st.button("👁️", key=f"view_{exam.id}", help="Xem chi tiết"):
                    show_exam_detail(exam.id)
            with a2:
                if st.button("📝", key=f"quiz_{exam.id}", help="Làm đề"):
                    st.session_state.start_quiz_exam_id = exam.id
                    st.switch_page("pages/8_📝_Lam_de.py")
            with a3:
                if st.button("🗑️", key=f"del_{exam.id}", help="Xóa đề"):
                    if store.delete(exam_id=exam.id):
                        st.success("Đã xóa!")
                        st.rerun()
                    else:
                        st.error("Lỗi xóa.")
        st.markdown("<hr style='margin: 0.5em 0; opacity: 0.3;'/>", unsafe_allow_html=True)

    # Pagination UI
    total_pages = max(1, (total_count + per_page - 1) // per_page)
    if total_pages > 1:
        p1, p2, p3 = st.columns([1, 2, 1])
        with p1:
            if st.button("⬅️ Trang trước") and st.session_state.current_page > 1:
                st.session_state.current_page -= 1
                st.rerun()
        with p2:
            st.markdown(f"<p style='text-align: center; padding-top: 10px;'>Trang <b>{st.session_state.current_page}</b> / {total_pages}</p>", unsafe_allow_html=True)
        with p3:
            if st.button("Trang sau ➡️") and st.session_state.current_page < total_pages:
                st.session_state.current_page += 1
                st.rerun()
