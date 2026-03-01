import streamlit as st

from backend.schemas.exam import SearchResult, Exam
from frontend.utils.ui_helpers import (
    subject_badge, difficulty_badge, question_type_badge,
    format_score, format_datetime, truncate_text,
    DIFFICULTY_LABELS, QUESTION_TYPE_LABELS,
)


def render_exam_card(result: SearchResult, index: int) -> None:
    q_type = result.exam.questions[0].question_type if result.exam.questions else "trac_nghiem"
    badges_html = (
        subject_badge(result.exam.subject)
        + difficulty_badge(result.exam.difficulty)
        + question_type_badge(q_type)
    )
    score_pct = int(result.score * 100)
    bar_color = "#4CAF50" if score_pct >= 70 else "#FF9800" if score_pct >= 40 else "#F44336"

    card_html = f"""
    <div class="exam-card">
        <h3 style="margin:0 0 8px 0;">{result.exam.title}</h3>
        <div>{badges_html}
            <span class="badge badge-info">{len(result.exam.questions)} câu</span>
        </div>
        <div class="progress-bar-container" style="margin-top:12px;">
            <div class="progress-bar" style="width:{score_pct}%; background-color:{bar_color};"></div>
        </div>
        <p style="text-align:right; margin:4px 0 0 0; font-size:0.9em; color:#757575;">
            Độ phù hợp: <b>{score_pct}%</b>
        </p>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)

    with st.expander(f"Xem chi tiết - {result.exam.title}"):
        if result.matched_questions:
            st.markdown("**Câu hỏi khớp nhất:**")
            for i, q in enumerate(result.matched_questions, 1):
                st.markdown(f"**Câu {i}:** {q.content}")
                if q.options:
                    for opt in q.options:
                        if q.answer and opt.startswith(q.answer):
                            st.markdown(f"- ✅ **{opt}**")
                        else:
                            st.markdown(f"- {opt}")
                if q.answer:
                    st.markdown(f"*Đáp án: {q.answer}*")
                st.divider()


def render_exam_detail(exam: Exam) -> None:
    st.markdown(f"### {exam.title}")
    q_type = exam.questions[0].question_type if exam.questions else "trac_nghiem"
    badges_html = (
        subject_badge(exam.subject)
        + difficulty_badge(exam.difficulty)
        + question_type_badge(q_type)
    )
    st.markdown(badges_html, unsafe_allow_html=True)
    st.markdown(f"**Số câu hỏi:** {len(exam.questions)} | **Ngày tạo:** {format_datetime(exam.created_at)}")
    if exam.source_file:
        st.markdown(f"**Nguồn:** {exam.source_file}")
    st.divider()

    for i, q in enumerate(exam.questions, 1):
        st.markdown(f"**Câu {i}:** {q.content}")
        if q.options:
            for opt in q.options:
                if q.answer and opt.startswith(q.answer):
                    st.markdown(f"- ✅ **{opt}**")
                else:
                    st.markdown(f"- {opt}")
        if q.answer:
            st.caption(f"Đáp án: {q.answer}")
        st.divider()

    # Export button
    export_text = f"Đề thi: {exam.title}\nMôn: {exam.subject}\n\n"
    for i, q in enumerate(exam.questions, 1):
        export_text += f"Câu {i}: {q.content}\n"
        for opt in q.options:
            export_text += f"  {opt}\n"
        if q.answer:
            export_text += f"  Đáp án: {q.answer}\n"
        export_text += "\n"

    st.download_button(
        label="⬇️ Tải xuống (TXT)",
        data=export_text,
        file_name=f"{exam.title}.txt",
        mime="text/plain",
        use_container_width=True,
    )
