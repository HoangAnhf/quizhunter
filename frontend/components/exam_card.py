import streamlit as st

from backend.schemas.exam import SearchResult, Exam
from frontend.utils.ui_helpers import (
    subject_badge, difficulty_badge, question_type_badge,
    format_score, format_datetime, truncate_text,
    DIFFICULTY_LABELS, QUESTION_TYPE_LABELS,
)


def _render_matching_columns(q) -> None:
    """Render câu nối cột dạng bảng 2 cột A | B."""
    if not q.column_a or not q.column_b:
        return
    rows = ""
    max_len = max(len(q.column_a), len(q.column_b))
    for i in range(max_len):
        left = f"{i+1}. {q.column_a[i]}" if i < len(q.column_a) else ""
        right = f"{chr(97+i)}. {q.column_b[i]}" if i < len(q.column_b) else ""
        rows += f"<tr><td style='padding:6px 12px;border:1px solid #ddd;'>{left}</td><td style='padding:6px 12px;border:1px solid #ddd;'>{right}</td></tr>"
    table_html = f"""
    <table style="width:100%;border-collapse:collapse;margin:8px 0;">
        <tr>
            <th style="padding:6px 12px;border:1px solid #ddd;background:#f0f2f6;text-align:left;width:50%;">Cột A</th>
            <th style="padding:6px 12px;border:1px solid #ddd;background:#f0f2f6;text-align:left;width:50%;">Cột B</th>
        </tr>
        {rows}
    </table>
    """
    st.markdown(table_html, unsafe_allow_html=True)


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
                if q.question_type == "noi_cot" and q.column_a and q.column_b:
                    _render_matching_columns(q)
                elif q.options:
                    for opt in q.options:
                        st.markdown(f"- {opt}")
                elif q.question_type == "tu_luan":
                    st.text_input(
                        "Nhập đáp án:",
                        key=f"card_{index}_match_{i}",
                        placeholder="Gõ đáp án của bạn...",
                    )
                if q.answer:
                    with st.popover("Xem đáp án"):
                        st.markdown(f"**Đáp án: {q.answer}**")
                st.divider()


def render_exam_detail(exam: Exam) -> None:
    st.markdown(f"### {exam.title}")
    if exam.exam_code:
        st.markdown(f"**Mã đề:** `{exam.exam_code}`")
    q_type = exam.questions[0].question_type if exam.questions else "trac_nghiem"
    badges_html = (
        subject_badge(exam.subject)
        + difficulty_badge(exam.difficulty)
        + question_type_badge(q_type)
    )
    st.markdown(badges_html, unsafe_allow_html=True)
    st.markdown(f"**Số câu hỏi:** {len(exam.questions)} | **Ngày tạo:** {format_datetime(exam.created_at)}")
    st.divider()

    for i, q in enumerate(exam.questions, 1):
        st.markdown(f"**Câu {i}:** {q.content}")
        if q.question_type == "noi_cot" and q.column_a and q.column_b:
            _render_matching_columns(q)
        elif q.options:
            for opt in q.options:
                st.markdown(f"- {opt}")
        elif q.question_type == "tu_luan":
            st.text_input(
                "Nhập đáp án:",
                key=f"detail_{exam.id}_{i}",
                placeholder="Gõ đáp án của bạn...",
            )
        if q.answer:
            with st.popover("Xem đáp án"):
                st.markdown(f"**Đáp án: {q.answer}**")
        st.divider()

    # Export button
    code_line = f"\nMã đề: {exam.exam_code}" if exam.exam_code else ""
    export_text = f"Đề thi: {exam.title}{code_line}\nMôn: {exam.subject}\n\n"
    for i, q in enumerate(exam.questions, 1):
        export_text += f"Câu {i}: {q.content}\n"
        if q.question_type == "noi_cot" and q.column_a and q.column_b:
            for j, item in enumerate(q.column_a):
                export_text += f"  {j+1}. {item}\n"
            export_text += "  ---\n"
            for j, item in enumerate(q.column_b):
                export_text += f"  {chr(97+j)}. {item}\n"
        else:
            for opt in q.options:
                export_text += f"  {opt}\n"
        if q.answer:
            export_text += f"  Đáp án: {q.answer}\n"
        export_text += "\n"

    # Nút in
    st.markdown(
        '<button onclick="window.print()" style="width:100%;padding:8px;margin-bottom:10px;'
        'background:#1E88E5;color:white;border:none;border-radius:6px;cursor:pointer;'
        'font-size:14px;">🖨️ In đề thi</button>',
        unsafe_allow_html=True,
    )

    dl1, dl2, dl3 = st.columns(3)
    with dl1:
        st.download_button(
            label="⬇️ TXT",
            data=export_text,
            file_name=f"{exam.title}.txt",
            mime="text/plain",
            use_container_width=True,
        )
    with dl2:
        try:
            from backend.services.exam_export import export_docx
            docx_data = export_docx(exam)
            st.download_button(
                label="⬇️ DOCX",
                data=docx_data,
                file_name=f"{exam.title}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True,
            )
        except Exception:
            st.button("⬇️ DOCX", disabled=True, use_container_width=True, help="Lỗi tạo DOCX")
    with dl3:
        try:
            from backend.services.exam_export import export_pdf
            pdf_data = export_pdf(exam)
            st.download_button(
                label="⬇️ PDF",
                data=pdf_data,
                file_name=f"{exam.title}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        except Exception:
            st.button("⬇️ PDF", disabled=True, use_container_width=True, help="Lỗi tạo PDF")
