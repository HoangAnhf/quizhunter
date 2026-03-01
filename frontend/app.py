import streamlit as st
import sys
from pathlib import Path

# Setup path to import backend correctly from root
root_path = Path(__file__).parent.parent
if str(root_path) not in sys.path:
    sys.path.append(str(root_path))

from frontend.utils.ui_helpers import load_css
from frontend.components.search_bar import render_search_bar
from backend.database.exam_store import ExamStore

st.set_page_config(
    page_title="QuizHunter - Trợ lý Tìm Đề Thi AI",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

load_css()

if "search_query" not in st.session_state:
    st.session_state.search_query = ""

# Header
st.markdown("<h1 style='text-align: center; color: #1E88E5;'>🎓 QuizHunter</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 1.2em; color: #616161;'>Trợ lý AI Tìm kiếm, Quản lý và Phân tích Đề thi thông minh</p>", unsafe_allow_html=True)
st.write("---")

# Fetch Stats
try:
    store = ExamStore()
    stats = store.get_stats()
except Exception:
    stats = {"total_exams": 0, "total_questions": 0, "subjects": {}, "difficulties": {}, "total_searches": 0}

# Metrics Cards
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f'<div class="metric-card"><h3>📚 Tổng đề thi</h3><h2>{stats.get("total_exams", 0)}</h2></div>', unsafe_allow_html=True)
with c2:
    st.markdown(f'<div class="metric-card"><h3>❓ Tổng câu hỏi</h3><h2>{stats.get("total_questions", 0)}</h2></div>', unsafe_allow_html=True)
with c3:
    st.markdown(f'<div class="metric-card"><h3>🏷️ Số môn học</h3><h2>{len(stats.get("subjects", {}))}</h2></div>', unsafe_allow_html=True)
with c4:
    st.markdown(f'<div class="metric-card"><h3>🔍 Lượt tìm kiếm</h3><h2>{stats.get("total_searches", 0)}</h2></div>', unsafe_allow_html=True)

st.write("---")

# Search Bar centered
st.markdown("<h3 style='text-align: center;'>Tìm kiếm ngữ nghĩa thông minh</h3>", unsafe_allow_html=True)
search_col1, search_col2, search_col3 = st.columns([1, 2, 1])
with search_col2:
    query = render_search_bar()
    if query:
        st.session_state.search_query = query
        st.switch_page("pages/1_🔍_Tim_kiem.py")