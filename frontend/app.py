import streamlit as st
import sys
from pathlib import Path

# Setup path to import backend correctly from root
root_path = Path(__file__).parent.parent
if str(root_path) not in sys.path:
    sys.path.append(str(root_path))

from frontend.utils.ui_helpers import load_css

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
@st.cache_resource(show_spinner=False)
def _get_store():
    from backend.database.mysql_store import MySQLExamStore
    return MySQLExamStore()

try:
    stats = _get_store().get_stats()
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

# Quick navigation
st.markdown("<h3 style='text-align: center;'>Truy cập nhanh</h3>", unsafe_allow_html=True)
nav1, nav2, nav3 = st.columns(3)
with nav1:
    if st.button("🔍 Tìm kiếm đề thi", use_container_width=True):
        st.switch_page("pages/1_🔍_Tim_kiem.py")
with nav2:
    if st.button("📚 Kho đề thi", use_container_width=True):
        st.switch_page("pages/3_📚_Kho_de.py")
with nav3:
    if st.button("🤖 Tạo đề bằng AI", use_container_width=True):
        st.switch_page("pages/6_🤖_Tao_de.py")

nav4, nav5, nav6 = st.columns(3)
with nav4:
    if st.button("📝 Làm đề thi", use_container_width=True):
        st.switch_page("pages/8_📝_Lam_de.py")
with nav5:
    if st.button("📈 Tiến trình học tập", use_container_width=True):
        st.switch_page("pages/9_📈_Tien_trinh.py")
with nav6:
    if st.button("📊 Dashboard", use_container_width=True):
        st.switch_page("pages/7_📊_Dashboard.py")