import streamlit as st
import sys
from pathlib import Path

root_path = Path(__file__).parent.parent.parent
if str(root_path) not in sys.path:
    sys.path.append(str(root_path))

from frontend.utils.ui_helpers import load_css, DIFFICULTY_LABELS

st.set_page_config(page_title="Tiến Trình Học Tập", page_icon="📈", layout="wide")
load_css()


@st.cache_resource(show_spinner=False)
def _get_store():
    from backend.database.mysql_store import MySQLExamStore
    return MySQLExamStore()


store = _get_store()

st.title("📈 Tiến Trình Học Tập")

try:
    stats = store.get_quiz_stats_summary()
except Exception as e:
    st.error(f"Lỗi kết nối: {e}")
    st.stop()

# ── Tổng quan ──
st.subheader("📊 Tổng quan")
c1, c2, c3 = st.columns(3)

total_mins = stats["total_time"] // 60
avg_10 = round(stats["avg_score"] / 10, 1) if stats["avg_score"] else 0
c1.metric("Tổng số lần làm đề", stats["total_sessions"])
c2.metric("Điểm trung bình", f"{avg_10}/10")
c3.metric("Tổng thời gian", f"{total_mins} phút")

if stats["total_sessions"] == 0:
    st.info("Bạn chưa làm đề nào. Hãy bắt đầu làm đề tại trang 📝 Làm đề!")
    if st.button("📝 Bắt đầu làm đề", use_container_width=True):
        st.switch_page("pages/8_📝_Lam_de.py")
    st.stop()

st.divider()

# ── Filter môn học ──
all_subjects = list(set(t["subject"] for t in stats["trend"])) if stats["trend"] else []
all_subjects.sort()

selected_subjects = st.multiselect(
    "🏷️ Lọc theo môn học",
    options=all_subjects,
    default=all_subjects,
    key="progress_subject_filter",
)

# ── Biểu đồ xu hướng điểm (cột + đường nối, thang 10) ──
st.subheader("📈 Xu hướng điểm số theo thời gian")
if stats["trend"]:
    import pandas as pd
    import altair as alt

    trend_data = stats["trend"][::-1]  # Reverse to chronological

    # Filter theo mon
    if selected_subjects:
        trend_data = [t for t in trend_data if t["subject"] in selected_subjects]

    if trend_data:
        df_trend = pd.DataFrame(trend_data)
        df_trend["completed_at"] = pd.to_datetime(df_trend["completed_at"])
        df_trend["Điểm"] = df_trend["pct"].apply(lambda x: round(float(x) / 10, 1))
        df_trend["Môn học"] = df_trend["subject"]
        df_trend["Ngày"] = df_trend["completed_at"].dt.strftime("%d/%m")
        df_trend["Chi tiết"] = df_trend["completed_at"].dt.strftime("%d/%m/%Y %H:%M")
        # Nhan truc X: "Lan 1" ngan gon
        df_trend["Lần"] = [f"Lần {i+1}" for i in range(len(df_trend))]

        n = len(df_trend)
        # Moi cot ~40px, be ngang vua phai giong hinh mau
        bar_size = 28
        # Khoang cach giua cac cot: step = bar_size + padding
        step = 45

        # Brush cho thanh keo
        brush = alt.selection_interval(encodings=["x"])

        # === CHART CHINH (chi cot, khong duong noi) ===
        bars_main = alt.Chart(df_trend).mark_bar(
            size=bar_size,
            cornerRadiusTopLeft=2,
            cornerRadiusTopRight=2,
        ).encode(
            x=alt.X("Lần:N", sort=None, title=None,
                     axis=alt.Axis(labelAngle=0, labelFontSize=11)),
            y=alt.Y("Điểm:Q",
                     scale=alt.Scale(domain=[0, 10]),
                     title="Điểm số",
                     axis=alt.Axis(values=list(range(11)), tickCount=11, grid=True)),
            color=alt.condition(
                brush,
                alt.Color("Môn học:N", legend=alt.Legend(title="Môn học")),
                alt.value("#d0d0d0"),
            ),
            tooltip=[
                alt.Tooltip("Chi tiết:N", title="Thời gian"),
                alt.Tooltip("Môn học:N"),
                alt.Tooltip("Điểm:Q", title="Điểm"),
            ],
        ).properties(
            height=400,
            width=alt.Step(step),
        )

        # === THANH KEO PHIA DUOI ===
        range_bar = alt.Chart(df_trend).mark_bar(
            size=12,
        ).encode(
            x=alt.X("Lần:N", sort=None,
                     axis=alt.Axis(
                         title="↔ Kéo chuột để chọn khoảng thời gian",
                         labelAngle=0, labelFontSize=9,
                     )),
            y=alt.Y("Điểm:Q", axis=None, scale=alt.Scale(domain=[0, 10])),
            color=alt.Color("Môn học:N", legend=None),
            opacity=alt.value(0.4),
        ).properties(
            height=60,
            width=alt.Step(step),
        ).add_params(brush)

        final_chart = alt.vconcat(
            bars_main, range_bar,
        ).resolve_scale(color="shared").configure_axis(
            gridColor="#e8e8e8",
        )

        st.altair_chart(final_chart)
    else:
        st.info("Không có dữ liệu cho các môn đã chọn.")
else:
    st.info("Chưa có dữ liệu.")

st.divider()

# ── Kết quả theo Môn học (full width, bỏ Phân bố) ──
st.subheader("📚 Kết quả theo Môn học")
if stats["by_subject"]:
    import pandas as pd
    import altair as alt

    by_sub = stats["by_subject"]
    if selected_subjects:
        by_sub = [s for s in by_sub if s["subject"] in selected_subjects]

    if by_sub:
        df_sub = pd.DataFrame(by_sub)
        df_sub["avg_score"] = df_sub["avg_score"].apply(lambda x: round(float(x) / 10, 1))
        df_sub = df_sub.rename(columns={
            "subject": "Môn học",
            "attempts": "Số lần làm",
            "avg_score": "Điểm TB",
        })
        st.dataframe(df_sub, use_container_width=True, hide_index=True)

        chart = alt.Chart(df_sub).mark_bar(
            size=30,
            cornerRadiusTopLeft=2,
            cornerRadiusTopRight=2,
        ).encode(
            x=alt.X("Môn học:N", axis=alt.Axis(labelAngle=0, labelFontSize=11)),
            y=alt.Y("Điểm TB:Q",
                     scale=alt.Scale(domain=[0, 10]),
                     title="Điểm TB (thang 10)",
                     axis=alt.Axis(values=list(range(11)), tickCount=11, grid=True)),
            color=alt.Color("Môn học:N", legend=None),
            tooltip=["Môn học", "Điểm TB", "Số lần làm"],
        ).properties(height=350, width=alt.Step(50))
        st.altair_chart(chart)

st.divider()

# ── Lịch sử làm đề ──
st.subheader("📋 Lịch sử làm đề")
history = store.get_quiz_history(30)

if selected_subjects:
    history = [h for h in history if h["subject"] in selected_subjects]

if not history:
    st.info("Chưa có lịch sử làm đề cho các môn đã chọn.")
else:
    for i, h in enumerate(history):
        pct = round(h["score"] / h["total"] * 100, 1) if h["total"] > 0 else 0
        score_10 = round(h["score"] / h["total"] * 10, 1) if h["total"] > 0 else 0
        mins, secs = divmod(h["time_spent_seconds"], 60)

        if pct >= 80:
            icon = "🟢"
        elif pct >= 60:
            icon = "🟡"
        elif pct >= 40:
            icon = "🟠"
        else:
            icon = "🔴"

        code_str = f"`{h['exam_code']}` " if h.get("exam_code") else ""
        completed = h["completed_at"]
        if not isinstance(completed, str):
            completed = completed.strftime("%d/%m/%Y %H:%M")

        col_info, col_score, col_detail = st.columns([4, 1.5, 1])
        with col_info:
            grade_str = f" | Lớp {h['grade']}" if h.get('grade') else ""
            st.markdown(
                f"{icon} {code_str}**{h['title']}** — "
                f"{h['subject']}{grade_str} | "
                f"⏱️ {mins}:{secs:02d}"
            )
            st.caption(f"{completed}")
        with col_score:
            st.markdown(f"**{score_10}/10** ({h['score']}/{h['total']})")
        with col_detail:
            if st.button("👁️", key=f"hist_{i}", use_container_width=True, help="Xem chi tiết"):
                st.session_state.view_session_id = h["id"]

        st.markdown("<hr style='margin:4px 0;opacity:0.15;'/>", unsafe_allow_html=True)

# ── Chi tiết 1 lần làm đề (dialog) ──
if "view_session_id" in st.session_state and st.session_state.view_session_id:
    @st.dialog("Chi tiết lần làm đề", width="large")
    def show_session_detail():
        import re
        sid = st.session_state.view_session_id
        detail = store.get_quiz_session_detail(sid)
        if not detail:
            st.error("Không tìm thấy.")
            return

        pct = round(detail["score"] / detail["total"] * 100, 1) if detail["total"] > 0 else 0
        mins, secs = divmod(detail["time_spent_seconds"], 60)

        st.markdown(f"### {detail['title']}")
        if detail.get("exam_code"):
            st.markdown(f"**Mã đề:** `{detail['exam_code']}`")
        st.markdown(f"**Điểm:** {detail['score']}/{detail['total']} ({pct}%) | **Thời gian:** {mins}:{secs:02d}")
        st.divider()

        for idx, a in enumerate(detail.get("answers", []), 1):
            icon = "✅" if a["is_correct"] else "❌"
            st.markdown(f"**{icon} Câu {idx}:** {a['content']}")

            options = a.get("options", [])
            for i, opt in enumerate(options):
                letter = chr(65 + i)
                clean = re.sub(r'^[A-Da-d\d][.)]\s*', '', opt)
                prefix = ""
                correct = a.get("correct_answer", "").strip().upper()
                user = (a.get("user_answer") or "").strip().upper()
                if letter == correct:
                    prefix = "✅ "
                elif letter == user and not a["is_correct"]:
                    prefix = "❌ "
                st.markdown(f"&emsp;{prefix}{letter}. {clean}")

            if not a["is_correct"]:
                st.markdown(f"&emsp;**➡️ Đáp án đúng: {a.get('correct_answer', '')}**")
            st.markdown("---")

        if st.button("Đóng", use_container_width=True):
            st.session_state.view_session_id = None
            st.rerun()

    show_session_detail()
