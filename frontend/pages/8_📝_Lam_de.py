import re
import uuid
import time
import streamlit as st
import sys
from pathlib import Path

root_path = Path(__file__).parent.parent.parent
if str(root_path) not in sys.path:
    sys.path.append(str(root_path))

from frontend.utils.ui_helpers import load_css, DIFFICULTY_LABELS

st.set_page_config(page_title="Làm Đề", page_icon="📝", layout="wide")
load_css()


@st.cache_resource(show_spinner=False)
def _get_store():
    from backend.database.mysql_store import MySQLExamStore
    return MySQLExamStore()


store = _get_store()

st.title("📝 Làm Đề Thi")

# ── States ──
if "quiz_phase" not in st.session_state:
    st.session_state.quiz_phase = "select"  # select | doing | result
if "quiz_exam" not in st.session_state:
    st.session_state.quiz_exam = None
if "quiz_session_id" not in st.session_state:
    st.session_state.quiz_session_id = None
if "quiz_start_time" not in st.session_state:
    st.session_state.quiz_start_time = None
if "quiz_answers" not in st.session_state:
    st.session_state.quiz_answers = {}
if "quiz_result" not in st.session_state:
    st.session_state.quiz_result = None
if "quiz_time_limit" not in st.session_state:
    st.session_state.quiz_time_limit = 0  # 0 = khong gioi han
if "quiz_submitted" not in st.session_state:
    st.session_state.quiz_submitted = False


def reset_quiz():
    st.session_state.quiz_phase = "select"
    st.session_state.quiz_exam = None
    st.session_state.quiz_session_id = None
    st.session_state.quiz_start_time = None
    st.session_state.quiz_answers = {}
    st.session_state.quiz_result = None
    st.session_state.quiz_time_limit = 0
    st.session_state.quiz_submitted = False


def _strip_option_prefix(opt: str) -> str:
    """Loai bo prefix 'A. ', 'B. ', '1. ' ... khoi dau option neu co."""
    return re.sub(r'^[A-Da-d\d][.)]\s*', '', opt)


def _detect_time_from_title(title: str) -> int:
    """Tự động phát hiện thời gian làm bài từ tên đề. Trả về phút, 0 nếu không tìm thấy."""
    m = re.search(r'(\d+)\s*(?:phút|phut|p\b|min)', title, re.IGNORECASE)
    if m:
        val = int(m.group(1))
        if 5 <= val <= 180:  # hợp lệ: 5 phút đến 3 giờ
            return val
    return 0


def _start_quiz(exam, time_limit_minutes=0):
    """Bat dau lam de tu bat ky trang nao."""
    gradable = [q for q in exam.questions if q.question_type == "trac_nghiem" and q.options and q.answer]
    if not gradable:
        return False

    # Tự động phát hiện thời gian từ tên đề nếu chưa set
    if time_limit_minutes == 0:
        time_limit_minutes = _detect_time_from_title(exam.title)

    session_id = str(uuid.uuid4())
    store.create_quiz_session(session_id, exam.id, len(gradable))
    st.session_state.quiz_exam = exam
    st.session_state.quiz_session_id = session_id
    st.session_state.quiz_start_time = time.time()
    st.session_state.quiz_answers = {}
    st.session_state.quiz_phase = "doing"
    st.session_state.quiz_time_limit = time_limit_minutes * 60  # seconds
    st.session_state.quiz_submitted = False
    return True


def _do_submit(gradable_qs):
    """Cham diem va luu ket qua."""
    time_spent = int(time.time() - st.session_state.quiz_start_time)
    score = 0
    answer_records = []
    for q in gradable_qs:
        user_ans = st.session_state.quiz_answers.get(q.id, "")
        correct_ans = q.answer.strip().upper()
        is_correct = user_ans.strip().upper() == correct_ans
        if is_correct:
            score += 1
        answer_records.append({
            "question_id": q.id,
            "user_answer": user_ans,
            "is_correct": is_correct,
        })
    store.save_quiz_answers(st.session_state.quiz_session_id, answer_records)
    store.complete_quiz_session(st.session_state.quiz_session_id, score, time_spent)
    st.session_state.quiz_result = {
        "score": score,
        "total": len(gradable_qs),
        "time_spent": time_spent,
        "answers": answer_records,
        "questions": gradable_qs,
    }
    st.session_state.quiz_phase = "result"


# ── Dialog xác nhận nộp bài ──
@st.dialog("📩 Xác nhận nộp bài")
def confirm_submit_dialog():
    exam = st.session_state.quiz_exam
    gradable_qs = [q for q in exam.questions if q.question_type == "trac_nghiem" and q.options and q.answer]
    answered = sum(1 for q in gradable_qs if q.id in st.session_state.quiz_answers)
    unanswered = len(gradable_qs) - answered
    elapsed = int(time.time() - st.session_state.quiz_start_time)
    time_limit = st.session_state.quiz_time_limit

    st.markdown("### 🤔 Bạn có chắc chắn muốn nộp bài?")

    if time_limit > 0:
        remaining = max(0, time_limit - elapsed)
        r_mins, r_secs = divmod(remaining, 60)
        st.info(f"⏱️ Bạn còn **{r_mins} phút {r_secs} giây** làm bài.")

    if unanswered > 0:
        st.warning(f"⚠️ Bạn còn **{unanswered} câu chưa trả lời**!")
    else:
        st.success(f"✅ Bạn đã trả lời đủ **{answered}/{len(gradable_qs)}** câu.")

    col_yes, col_no = st.columns(2)
    with col_yes:
        if st.button("✅ Có, nộp bài", type="primary", use_container_width=True):
            st.session_state.quiz_submitted = False
            _do_submit(gradable_qs)
            st.rerun()
    with col_no:
        if st.button("❌ Không, làm tiếp", use_container_width=True):
            st.session_state.quiz_submitted = False
            st.rerun()


# ── Nhan de tu trang khac (Tim kiem / Tao de) ──
if "start_quiz_exam_id" in st.session_state and st.session_state.start_quiz_exam_id:
    exam_id = st.session_state.start_quiz_exam_id
    st.session_state.start_quiz_exam_id = None
    exam = store.get_by_id(exam_id)
    if exam:
        if _start_quiz(exam):
            st.rerun()
        else:
            st.warning("Đề thi này không có câu trắc nghiệm để làm bài.")


# ════════════════════════════════════════════════════════════
# PHASE 1: Chọn đề thi
# ════════════════════════════════════════════════════════════
if st.session_state.quiz_phase == "select":
    st.markdown("### Chọn đề thi để làm bài")

    from config import VI_SUBJECTS, DIFFICULTIES, GRADES

    col1, col2, col3, col4 = st.columns([2, 2, 1.5, 1.5])
    with col1:
        sel_subject = st.selectbox("Môn học", ["Tất cả"] + VI_SUBJECTS, key="quiz_sel_sub")
    with col2:
        sel_diff_label = st.selectbox("Mức độ", ["Tất cả"] + [DIFFICULTY_LABELS.get(d, d) for d in DIFFICULTIES], key="quiz_sel_diff")
    with col3:
        sel_grade = st.selectbox("Lớp", ["Tất cả"] + [f"Lớp {g}" for g in GRADES], key="quiz_sel_grade")
    with col4:
        time_limit = st.selectbox("Thời gian", [0, 15, 30, 45, 60, 90], format_func=lambda x: "Không giới hạn" if x == 0 else f"{x} phút", key="quiz_time_limit_sel")

    f_sub = None if sel_subject == "Tất cả" else sel_subject
    _matched = next((k for k, v in DIFFICULTY_LABELS.items() if v == sel_diff_label), None) if sel_diff_label != "Tất cả" else None
    f_diff = None if _matched == "hon_hop" else _matched
    f_grade = int(sel_grade.replace("Lớp ", "")) if sel_grade != "Tất cả" else None

    search_q = st.text_input("🔍 Tìm đề", placeholder="Nhập mã đề hoặc tên đề...", key="quiz_search")

    try:
        if search_q and search_q.strip():
            exams, total = store.search_by_code_or_title(
                query=search_q.strip(), subject=f_sub, difficulty=f_diff, grade=f_grade,
                page=1, per_page=20,
            )
        else:
            exams = store.get_all(subject=f_sub, difficulty=f_diff, grade=f_grade, page=1, per_page=20)
            total = store.count(subject=f_sub, difficulty=f_diff, grade=f_grade)
    except Exception as e:
        st.error(f"Lỗi: {e}")
        exams, total = [], 0

    if not exams:
        st.info("Không có đề thi nào. Hãy thêm đề vào Kho đề trước.")
    else:
        st.caption(f"Tìm thấy {total} đề thi")
        for exam in exams:
            mc_count = sum(1 for q in exam.questions if q.question_type == "trac_nghiem")

            col_info, col_btn = st.columns([4, 1])
            with col_info:
                code_str = f"`{exam.exam_code}` " if exam.exam_code else ""
                grade_str = f" | Lớp {exam.grade}" if exam.grade else ""
                st.markdown(
                    f"**{code_str}{exam.title}** — "
                    f"{exam.subject} | {DIFFICULTY_LABELS.get(exam.difficulty, exam.difficulty)}{grade_str} | "
                    f"**{mc_count}** câu trắc nghiệm"
                )
            with col_btn:
                if st.button("📝 Làm bài", key=f"start_{exam.id}", use_container_width=True):
                    if _start_quiz(exam, time_limit):
                        st.rerun()
                    else:
                        st.warning("Đề này không có câu trắc nghiệm.")
            st.markdown("<hr style='margin:4px 0;opacity:0.15;'/>", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
# PHASE 2: Làm bài
# ════════════════════════════════════════════════════════════
elif st.session_state.quiz_phase == "doing":
    exam = st.session_state.quiz_exam
    gradable_qs = [q for q in exam.questions if q.question_type == "trac_nghiem" and q.options and q.answer]

    # Header
    code_str = f" ({exam.exam_code})" if exam.exam_code else ""
    st.markdown(f"### {exam.title}{code_str}")
    st.caption(f"{exam.subject} | {DIFFICULTY_LABELS.get(exam.difficulty, exam.difficulty)} | {len(gradable_qs)} câu trắc nghiệm")

    # ── Timer (auto-refresh mỗi giây khi có time limit) ──
    elapsed = int(time.time() - st.session_state.quiz_start_time)
    time_limit = st.session_state.quiz_time_limit

    if time_limit > 0:
        # Auto-refresh mỗi giây để đếm ngược
        from streamlit_autorefresh import st_autorefresh
        st_autorefresh(interval=1000, key="quiz_timer_refresh")

        remaining = max(0, time_limit - elapsed)
        r_mins, r_secs = divmod(remaining, 60)
        total_mins = time_limit // 60
        pct_remaining = remaining / time_limit

        if remaining <= 0:
            st.error("⏰ Hết giờ! Bài thi đã được nộp tự động.")
            _do_submit(gradable_qs)
            st.rerun()
        elif remaining <= 300:
            # Duoi 5 phut → do
            st.markdown(f"""
            <div style="background:#FFEBEE;border:2px solid #F44336;padding:12px 18px;border-radius:10px;margin-bottom:12px;">
                <div style="display:flex;align-items:center;justify-content:space-between;">
                    <div>
                        <span style="font-size:1.5em;">🚨</span>
                        <b style="color:#D32F2F;font-size:1.3em;"> {r_mins:02d}:{r_secs:02d}</b>
                    </div>
                    <span style="color:#D32F2F;font-weight:bold;">⚠️ Sắp hết giờ!</span>
                </div>
                <div style="background:#ffcdd2;border-radius:4px;height:6px;margin-top:8px;">
                    <div style="background:#D32F2F;height:100%;border-radius:4px;width:{pct_remaining*100:.0f}%;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="background:#E3F2FD;border:2px solid #1E88E5;padding:12px 18px;border-radius:10px;margin-bottom:12px;">
                <div style="display:flex;align-items:center;justify-content:space-between;">
                    <div>
                        <span style="font-size:1.5em;">⏱️</span>
                        <b style="color:#1565C0;font-size:1.3em;"> {r_mins:02d}:{r_secs:02d}</b>
                    </div>
                    <span style="color:#1565C0;">Tổng: {total_mins} phút</span>
                </div>
                <div style="background:#BBDEFB;border-radius:4px;height:6px;margin-top:8px;">
                    <div style="background:#1E88E5;height:100%;border-radius:4px;width:{pct_remaining*100:.0f}%;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        e_mins, e_secs = divmod(elapsed, 60)
        st.markdown(f"""
        <div style="background:#E3F2FD;border:2px solid #1E88E5;padding:12px 18px;border-radius:10px;margin-bottom:12px;">
            <span style="font-size:1.5em;">⏱️</span>
            <b style="color:#1565C0;font-size:1.3em;"> {e_mins:02d}:{e_secs:02d}</b>
            <span style="color:#666;margin-left:8px;">Không giới hạn</span>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # ── Render câu hỏi ──
    for idx, q in enumerate(gradable_qs):
        st.markdown(f"**Câu {idx + 1}:** {q.content}")

        option_labels = []
        for i, opt in enumerate(q.options):
            clean = _strip_option_prefix(opt)
            label = f"{chr(65 + i)}. {clean}"
            option_labels.append(label)

        current_answer = st.session_state.quiz_answers.get(q.id)
        default_idx = None
        if current_answer:
            for i in range(len(q.options)):
                if chr(65 + i) == current_answer.strip().upper():
                    default_idx = i
                    break

        selected = st.radio(
            f"Chọn đáp án câu {idx + 1}:",
            options=option_labels,
            index=default_idx,
            key=f"q_{idx}_{q.id}",
            label_visibility="collapsed",
        )

        if selected:
            st.session_state.quiz_answers[q.id] = selected.split(". ", 1)[0]

        st.markdown("---")

    # Progress
    answered = sum(1 for q in gradable_qs if q.id in st.session_state.quiz_answers)
    st.progress(answered / len(gradable_qs), text=f"Đã trả lời {answered}/{len(gradable_qs)}")

    col_submit, col_cancel = st.columns(2)
    with col_submit:
        if st.button("📩 Nộp bài", type="primary", use_container_width=True, disabled=(answered == 0)):
            st.session_state.quiz_submitted = True
            st.rerun()

    with col_cancel:
        if st.button("❌ Hủy bỏ", use_container_width=True):
            reset_quiz()
            st.rerun()

    # Hiện dialog xác nhận
    if st.session_state.quiz_submitted:
        confirm_submit_dialog()


# ════════════════════════════════════════════════════════════
# PHASE 3: Kết quả
# ════════════════════════════════════════════════════════════
elif st.session_state.quiz_phase == "result":
    exam = st.session_state.quiz_exam
    result = st.session_state.quiz_result
    score = result["score"]
    total = result["total"]
    pct = round(score / total * 100, 1) if total > 0 else 0
    mins, secs = divmod(result["time_spent"], 60)

    # Score banner với robot emotions
    if pct >= 80:
        color = "#4CAF50"
        robot = "🤖✨"
        msg = "Xuất sắc! Bạn đã hoàn thành rất tốt!"
        sub_msg = "Tiếp tục phát huy nhé! 🌟"
    elif pct >= 60:
        color = "#FF9800"
        robot = "🤖😊"
        msg = "Khá tốt! Bạn đang tiến bộ!"
        sub_msg = "Cố gắng thêm một chút nữa để đạt xuất sắc! 💪"
    elif pct >= 40:
        color = "#FF5722"
        robot = "🤖😐"
        msg = "Trung bình. Bạn cần ôn tập thêm."
        sub_msg = "Hãy xem lại các câu sai và thử lại nhé! 📖"
    elif pct >= 25:
        color = "#F44336"
        robot = "🤖😟"
        msg = "Bạn cần cố gắng hơn!"
        sub_msg = "Đừng nản chí, hãy ôn lại kiến thức và thử lại! 📚"
    else:
        color = "#B71C1C"
        robot = "🤖😢"
        msg = "Kết quả chưa tốt. Bạn cần ôn tập nhiều hơn."
        sub_msg = "Hãy quay lại ôn lại bài và làm lại đề này nhé! Đừng bỏ cuộc! 💪📖"

    st.markdown(f"""
    <div style="text-align:center;padding:30px;background:{color}15;border:2px solid {color}44;border-radius:16px;margin-bottom:20px;">
        <div style="font-size:4em;margin-bottom:10px;">{robot}</div>
        <h1 style="color:{color};margin:0;font-size:3em;">{score}/{total}</h1>
        <h2 style="color:{color};margin:8px 0;">{pct}%</h2>
        <h3 style="color:{color};margin:5px 0;">{msg}</h3>
        <p style="color:#666;font-size:1.1em;">{sub_msg}</p>
        <p style="color:#999;margin-top:10px;">⏱️ Thời gian: {mins} phút {secs} giây</p>
    </div>
    """, unsafe_allow_html=True)

    # Metrics
    c1, c2, c3 = st.columns(3)
    c1.metric("✅ Đúng", f"{score} câu")
    c2.metric("❌ Sai", f"{total - score} câu")
    c3.metric("⏱️ Thời gian", f"{mins}:{secs:02d}")

    st.divider()

    # Chi tiết từng câu
    st.subheader("📋 Chi tiết đáp án")
    questions = result["questions"]
    answers = result["answers"]

    for idx, (q, a) in enumerate(zip(questions, answers)):
        icon = "✅" if a["is_correct"] else "❌"
        st.markdown(f"**{icon} Câu {idx + 1}:** {q.content}")

        if q.options:
            for i, opt in enumerate(q.options):
                letter = chr(65 + i)
                clean = _strip_option_prefix(opt)
                prefix = ""
                if letter == q.answer.strip().upper():
                    prefix = "✅ "
                elif letter == a["user_answer"].strip().upper() and not a["is_correct"]:
                    prefix = "❌ "
                st.markdown(f"&emsp;{prefix}{letter}. {clean}")

        if not a["is_correct"]:
            st.markdown(f"&emsp;**➡️ Đáp án đúng: {q.answer}**")
        st.markdown("---")

    # Actions
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🔄 Làm lại đề này", use_container_width=True):
            exam_copy = st.session_state.quiz_exam
            if _start_quiz(exam_copy):
                st.rerun()
    with col2:
        if st.button("📚 Chọn đề khác", use_container_width=True):
            reset_quiz()
            st.rerun()
    with col3:
        if st.button("📈 Xem tiến trình", use_container_width=True):
            st.switch_page("pages/9_📈_Tien_trinh.py")
