import streamlit as st
import sys
import uuid
from datetime import datetime
from pathlib import Path

root_path = Path(__file__).parent.parent.parent
if str(root_path) not in sys.path:
    sys.path.append(str(root_path))

from frontend.utils.ui_helpers import load_css, DIFFICULTY_LABELS, QUESTION_TYPE_LABELS
from config import SUBJECTS, DIFFICULTIES

st.set_page_config(page_title="Crawl Đề Thi", page_icon="🌐", layout="wide")
load_css()

st.title("🌐 Crawl Đề Thi từ Web")
st.markdown("Nhập URL trang web chứa đề thi để tự động trích xuất câu hỏi.")

# ── Hướng dẫn sử dụng (ẩn mặc định) ──
with st.expander("📖 Hướng dẫn sử dụng Crawl đề", expanded=False):
    st.markdown("""
### Crawl đề là gì?
Crawler sẽ tự động truy cập trang web bạn nhập, phân tích nội dung HTML và trích xuất các câu hỏi trắc nghiệm/tự luận.

### Trang web nào crawl được?
- Trang có câu hỏi **đánh số rõ ràng**: `Câu 1:`, `Câu 2:`, `1.`, `2.`...
- Trang có **đáp án A/B/C/D** viết dạng: `A.`, `B)`, `C:`, `D -`
- Trang **HTML tĩnh** (nội dung hiển thị ngay khi tải)

### Trang web nào KHÔNG crawl được?
- Trang dùng **JavaScript để tải nội dung** (React, Vue, Angular) — nội dung trống khi tắt JS
- Trang **yêu cầu đăng nhập** — crawler không thể login
- Trang **chặn bot** (trả lỗi 403 Forbidden)
- File **PDF, DOCX** — hãy dùng chức năng **Upload** thay thế

### Mẹo để crawl thành công
1. **Mở trang web trước** → kiểm tra có hiển thị câu hỏi không
2. **Copy URL của trang chứa đề thi cụ thể**, không phải trang danh sách
3. Nếu crawl thất bại → **copy nội dung đề thi** từ trang web → dán vào **Upload > Nhập trực tiếp**

### Định dạng câu hỏi được hỗ trợ
```
Câu 1: Nội dung câu hỏi ở đây?
A. Đáp án A
B. Đáp án B
C. Đáp án C
D. Đáp án D
Đáp án: B
```
""")

if "crawl_questions" not in st.session_state:
    st.session_state.crawl_questions = []
    st.session_state.crawl_title = ""
    st.session_state.crawl_url = ""

# Input URL — dùng form để mỗi lần submit luôn reset kết quả cũ
with st.form(key="crawl_form"):
    url = st.text_input(
        "URL trang web",
        value="",
        placeholder="https://example.com/de-thi-toan-lop-12",
    )
    submitted = st.form_submit_button("🔍 Crawl & Trích xuất", type="primary", use_container_width=True)

if submitted:
    if not url:
        st.error("Vui lòng nhập URL!")
    else:
        # Reset kết quả cũ ngay lập tức
        st.session_state.crawl_questions = []
        st.session_state.crawl_title = ""
        st.session_state.crawl_url = url

        with st.spinner("🔄 Đang tải và phân tích trang web (có thể crawl nhiều trang con)..."):
            from backend.services.web_crawler import ExamCrawler
            crawler = ExamCrawler()
            result = crawler.crawl_url(url)

        # Hiện các URL đã crawl
        crawled = result.get("crawled_urls", [])
        if len(crawled) > 1:
            st.caption(f"🌐 Đã crawl {len(crawled)} trang: {', '.join(crawled[:5])}")

        if result["error"]:
            st.error(f"❌ {result['error']}")
            if result.get("diagnosis"):
                with st.expander("🔍 Chi tiết lỗi & Gợi ý", expanded=True):
                    for d in result["diagnosis"]:
                        st.markdown(d)

        elif not result["questions"]:
            st.warning("⚠️ Không trích xuất được câu hỏi từ trang web này.")
            if result.get("diagnosis"):
                with st.expander("🔍 Phân tích & Gợi ý", expanded=True):
                    for d in result["diagnosis"]:
                        st.markdown(d)

            # Hiển thị link gợi ý để user thử crawl
            suggested = result.get("suggested_links", [])
            if suggested:
                with st.expander(f"🔗 {len(suggested)} link có thể chứa đề thi — thử crawl?", expanded=True):
                    st.caption("Bấm vào link để xem trước, hoặc copy URL rồi dán lại vào ô Crawl.")
                    for i, link in enumerate(suggested):
                        col_link, col_copy = st.columns([4, 1])
                        with col_link:
                            # Hiện URL rút gọn
                            from urllib.parse import urlparse
                            p = urlparse(link)
                            short = p.netloc + (p.path[:50] + "..." if len(p.path) > 50 else p.path)
                            st.markdown(f"[{short}]({link})")
                        with col_copy:
                            st.code(link, language=None)

            if result.get("raw_text"):
                with st.expander("📄 Xem nội dung text đã trích xuất", expanded=False):
                    st.text(result["raw_text"][:3000])

        else:
            st.success(f"✅ Tìm thấy **{len(result['questions'])} câu hỏi**!")
            mc_count = sum(1 for q in result["questions"] if q.question_type == "trac_nghiem")
            essay_count = sum(1 for q in result["questions"] if q.question_type == "tu_luan")
            has_answer = sum(1 for q in result["questions"] if q.answer)
            st.caption(f"📊 {mc_count} trắc nghiệm, {essay_count} tự luận | {has_answer}/{len(result['questions'])} câu có đáp án")

            st.session_state.crawl_questions = result["questions"]
            st.session_state.crawl_title = result["title"]

# Hiển thị kết quả crawl
if st.session_state.crawl_questions:
    st.subheader(f"📋 Kết quả: {len(st.session_state.crawl_questions)} câu hỏi")

    with st.expander("👁️ Xem trước câu hỏi", expanded=True):
        for i, q in enumerate(st.session_state.crawl_questions, 1):
            q_type = QUESTION_TYPE_LABELS.get(q.question_type, q.question_type)
            st.markdown(f"**Câu {i}** ({q_type}): {q.content}")
            if q.options:
                for opt in q.options:
                    st.markdown(f"  - {opt}")
            elif q.question_type == "tu_luan":
                st.text_input(
                    "Nhập đáp án:",
                    key=f"crawl_fill_{i}",
                    placeholder="Gõ đáp án của bạn...",
                )
            if q.answer:
                with st.popover("Xem đáp án"):
                    st.markdown(f"**Đáp án: {q.answer}**")
            st.divider()

    # Metadata
    st.subheader("📝 Thông tin đề thi")
    col1, col2 = st.columns(2)
    with col1:
        crawl_title = st.text_input("Tên đề thi", value=st.session_state.crawl_title)
        crawl_subject = st.selectbox("Môn học", ["Tự động phát hiện"] + SUBJECTS, key="crawl_subject")
    with col2:
        crawl_diff = st.selectbox(
            "Mức độ",
            ["Tự động phát hiện"] + [DIFFICULTY_LABELS.get(d, d) for d in DIFFICULTIES],
            key="crawl_diff",
        )

    if st.button("💾 Lưu vào Kho Đề", type="primary", use_container_width=True):
        if not crawl_title:
            st.error("Vui lòng nhập tên đề thi!")
        else:
            with st.spinner("Đang lưu..."):
                try:
                    # Auto classify nếu cần
                    final_subject = crawl_subject
                    final_diff = next(
                        (k for k, v in DIFFICULTY_LABELS.items() if v == crawl_diff),
                        None,
                    )

                    if crawl_subject == "Tự động phát hiện" or crawl_diff == "Tự động phát hiện":
                        from backend.core.classifier import ExamClassifier
                        classifier = ExamClassifier()
                        classification = classifier.classify(
                            questions=st.session_state.crawl_questions
                        )
                        if crawl_subject == "Tự động phát hiện":
                            final_subject = classification.get("subject", SUBJECTS[0])
                        if crawl_diff == "Tự động phát hiện":
                            final_diff = classification.get("difficulty", DIFFICULTIES[0])

                    from backend.database.mysql_store import MySQLExamStore
                    from backend.schemas.exam import Exam
                    store = MySQLExamStore()
                    new_exam = Exam(
                        id=str(uuid.uuid4()),
                        title=crawl_title,
                        subject=final_subject if final_subject != "Tự động phát hiện" else SUBJECTS[0],
                        difficulty=final_diff if final_diff else DIFFICULTIES[0],
                        questions=st.session_state.crawl_questions,
                        source_file=st.session_state.crawl_url,
                        created_at=datetime.utcnow().isoformat() + "Z",
                    )
                    exam_id = store.save(exam=new_exam)
                    st.success(f"✅ Đã lưu thành công! (ID: {exam_id})")
                    st.session_state.crawl_questions = []
                    st.session_state.crawl_title = ""
                except Exception as e:
                    st.error(f"Lỗi khi lưu: {e}")
