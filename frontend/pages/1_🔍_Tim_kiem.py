import streamlit as st
import sys
from pathlib import Path

root_path = Path(__file__).parent.parent.parent
if str(root_path) not in sys.path:
    sys.path.append(str(root_path))

from frontend.utils.ui_helpers import load_css
from frontend.components.search_bar import render_search_bar
from frontend.components.sidebar import render_sidebar_filters
from frontend.components.exam_card import render_exam_card
from backend.core.search_engine import SearchEngine

st.set_page_config(page_title="Tìm kiếm Đề Thi", page_icon="🔍", layout="wide")
load_css()

if "search_query" not in st.session_state:
    st.session_state.search_query = ""

filters = render_sidebar_filters()

st.title("🔍 Tìm kiếm Đề Thi")

# Search Interface
query = render_search_bar(placeholder="Nhập nội dung đề thi, khái niệm, câu hỏi...")
active_query = query if query else st.session_state.search_query

if active_query:
    st.session_state.search_query = active_query

    with st.spinner("AI đang phân tích và tìm kiếm ngữ nghĩa..."):
        try:
            search_engine = SearchEngine()
            results = search_engine.search(
                query=active_query,
                subject=filters["subject"],
                difficulty=filters["difficulty"],
                question_type=filters["question_type"],
                top_k=filters["top_k"]
            )

            if not results:
                st.warning("Không tìm thấy đề thi phù hợp. Vui lòng thử từ khóa hoặc nới lỏng bộ lọc.")
            else:
                st.success(f"Tìm thấy {len(results)} kết quả phù hợp nhất.")
                for i, res in enumerate(results):
                    render_exam_card(res, i)
        except Exception as e:
            st.error(f"Đã xảy ra lỗi khi tìm kiếm: {e}")
else:
    st.info("Nhập từ khóa vào thanh tìm kiếm ở trên để bắt đầu.")