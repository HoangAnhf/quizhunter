import streamlit as st
import sys
from pathlib import Path

root_path = Path(__file__).parent.parent.parent
if str(root_path) not in sys.path:
    sys.path.append(str(root_path))

from frontend.utils.ui_helpers import load_css, DIFFICULTY_LABELS

st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")
load_css()

st.title("📊 Dashboard Thống Kê")


@st.cache_resource(show_spinner=False)
def _get_store():
    from backend.database.mysql_store import MySQLExamStore
    return MySQLExamStore()


@st.cache_data(ttl=60)
def _get_dashboard_data():
    """Fetch all dashboard data in one go, cached for 60 seconds."""
    import mysql.connector
    from config import MYSQL_CONFIG
    conn = mysql.connector.connect(**MYSQL_CONFIG)
    cur = conn.cursor()

    # Grade distribution
    cur.execute("SELECT grade, COUNT(*) FROM questions GROUP BY grade ORDER BY grade")
    grade_data = cur.fetchall()

    # Top 10 exams
    cur.execute("""
        SELECT e.title, e.subject, e.difficulty, e.grade, COUNT(eq.question_id) as cnt
        FROM exams e LEFT JOIN exam_questions eq ON e.id = eq.exam_id
        GROUP BY e.id ORDER BY cnt DESC LIMIT 10
    """)
    top_exams = cur.fetchall()

    # Question types
    cur.execute("SELECT question_type, COUNT(*) FROM questions GROUP BY question_type")
    type_data = cur.fetchall()

    # Source distribution
    cur.execute("""
        SELECT COALESCE(source_file, 'Không rõ') as src, COUNT(*)
        FROM exams GROUP BY src ORDER BY COUNT(*) DESC LIMIT 10
    """)
    src_data = cur.fetchall()

    cur.close()
    conn.close()

    return {
        "grade_data": grade_data,
        "top_exams": top_exams,
        "type_data": type_data,
        "src_data": src_data,
    }


store = _get_store()

try:
    stats = store.get_stats()
except Exception as e:
    st.error(f"Lỗi kết nối MySQL: {e}")
    st.stop()

# --- Tổng quan ---
st.subheader("Tổng quan")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Tổng câu hỏi", stats.get("total_questions", 0))
c2.metric("Tổng đề thi", stats.get("total_exams", 0))
c3.metric("Số môn học", len(stats.get("subjects", {})))
c4.metric("Số mức độ", len(stats.get("difficulties", {})))

st.write("---")

# --- Biểu đồ ---
col_left, col_right = st.columns(2)

# Câu hỏi theo môn
with col_left:
    st.subheader("Câu hỏi theo Môn học")
    subjects = stats.get("subjects", {})
    if subjects:
        import pandas as pd
        df_sub = pd.DataFrame(
            sorted(subjects.items(), key=lambda x: x[1], reverse=True),
            columns=["Môn học", "Số câu"]
        )
        st.bar_chart(df_sub.set_index("Môn học"))
    else:
        st.info("Chưa có dữ liệu.")

# Câu hỏi theo mức độ
with col_right:
    st.subheader("Câu hỏi theo Mức độ")
    diffs = stats.get("difficulties", {})
    if diffs:
        import pandas as pd
        df_diff = pd.DataFrame(
            [(DIFFICULTY_LABELS.get(k, k), v) for k, v in diffs.items()],
            columns=["Mức độ", "Số câu"]
        )
        st.bar_chart(df_diff.set_index("Mức độ"))
    else:
        st.info("Chưa có dữ liệu.")

st.write("---")

# --- Detailed charts from cached data ---
try:
    dashboard = _get_dashboard_data()

    # Phân bố theo lớp
    st.subheader("Câu hỏi theo Lớp")
    if dashboard["grade_data"]:
        import pandas as pd
        df_grade = pd.DataFrame(dashboard["grade_data"], columns=["Lớp", "Số câu"])
        df_grade["Lớp"] = df_grade["Lớp"].apply(lambda x: f"Lớp {x}")
        st.bar_chart(df_grade.set_index("Lớp"))

    # Top 10 đề nhiều câu nhất
    st.write("---")
    st.subheader("Top 10 đề thi nhiều câu nhất")
    if dashboard["top_exams"]:
        import pandas as pd
        df_top = pd.DataFrame(dashboard["top_exams"], columns=["Tên đề", "Môn", "Mức độ", "Lớp", "Số câu"])
        df_top["Mức độ"] = df_top["Mức độ"].map(DIFFICULTY_LABELS).fillna(df_top["Mức độ"])
        df_top["Lớp"] = df_top["Lớp"].apply(lambda x: f"Lớp {x}" if x else "—")
        st.dataframe(df_top, use_container_width=True, hide_index=True)

    # Loại câu hỏi + Nguồn
    st.write("---")
    col_type, col_source = st.columns(2)

    with col_type:
        st.subheader("Theo Loại câu hỏi")
        if dashboard["type_data"]:
            from frontend.utils.ui_helpers import QUESTION_TYPE_LABELS
            import pandas as pd
            df_type = pd.DataFrame(dashboard["type_data"], columns=["Loại", "Số câu"])
            df_type["Loại"] = df_type["Loại"].map(QUESTION_TYPE_LABELS).fillna(df_type["Loại"])
            st.bar_chart(df_type.set_index("Loại"))

    with col_source:
        st.subheader("Đề thi theo Nguồn")
        if dashboard["src_data"]:
            import pandas as pd
            df_src = pd.DataFrame(dashboard["src_data"], columns=["Nguồn", "Số đề"])
            st.dataframe(df_src, use_container_width=True, hide_index=True)

except Exception as e:
    st.warning(f"Lỗi truy vấn chi tiết: {e}")
