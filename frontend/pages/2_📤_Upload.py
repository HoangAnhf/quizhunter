import streamlit as st
import sys
import uuid
from datetime import datetime
from pathlib import Path

root_path = Path(__file__).parent.parent.parent
if str(root_path) not in sys.path:
    sys.path.append(str(root_path))

from frontend.utils.ui_helpers import load_css, DIFFICULTY_LABELS, QUESTION_TYPE_LABELS
from config import SUBJECTS, DIFFICULTIES, QUESTION_TYPES, SUPPORTED_FORMATS

st.set_page_config(page_title="Upload Đề Thi", page_icon="📤", layout="wide")
load_css()

st.title("📤 Upload Đề Thi Mới")

if "upload_questions" not in st.session_state:
    st.session_state.upload_questions = []
    st.session_state.temp_exam_info = {}
if "voice_input_text" not in st.session_state:
    st.session_state.voice_input_text = ""

tab1, tab2 = st.tabs(["📁 Upload File", "📝 Nhập trực tiếp"])
file_bytes = None
file_name = None
raw_text = None

with tab1:
    st.markdown("Hỗ trợ định dạng: " + ", ".join(SUPPORTED_FORMATS))
    allowed_types = [fmt.replace('.', '') for fmt in SUPPORTED_FORMATS]
    uploaded_files = st.file_uploader("Kéo thả file vào đây", type=allowed_types, accept_multiple_files=True)
    if uploaded_files:
        st.success(f"Đã tải lên {len(uploaded_files)} file. Sẽ xử lý file: **{uploaded_files[0].name}**")
        file_bytes = uploaded_files[0].getvalue()
        file_name = uploaded_files[0].name

with tab2:
    # Voice Input
    with st.expander("🎤 Nhập bằng giọng nói", expanded=False):
        st.caption("Bấm nút → đọc nội dung đề thi → bấm lại để dừng. Có thể ghi nhiều lần, text sẽ nối tiếp.")
        try:
            from streamlit_mic_recorder import speech_to_text

            voice_text = speech_to_text(
                start_prompt="🎤 Bấm để ghi âm",
                stop_prompt="⏹️ Bấm để dừng",
                just_once=False,
                use_container_width=True,
                language="vi-VN",
                key="voice_upload",
            )

            if voice_text:
                st.success(f'✅ Nhận dạng được: "{voice_text}"')
                if st.session_state.voice_input_text:
                    st.session_state.voice_input_text += "\n" + voice_text
                else:
                    st.session_state.voice_input_text = voice_text
                st.info(f'📝 Đã thêm vào nội dung đề thi.')
        except ImportError:
            st.warning(
                "Cần cài đặt streamlit-mic-recorder: `pip install streamlit-mic-recorder`"
            )

    # Text area với voice text đã nhận dạng
    default_text = st.session_state.voice_input_text
    raw_text = st.text_area(
        "Nội dung đề thi", height=250,
        value=default_text,
        placeholder="Câu 1: Streamlit là gì?\nA. Framework Frontend\nB. Cơ sở dữ liệu..."
    )

st.subheader("📝 Thông tin bổ sung")
col1, col2 = st.columns(2)
with col1:
    exam_title = st.text_input("Tên đề thi (*)")
    exam_subject = st.selectbox("Môn học", ["Chưa rõ"] + SUBJECTS)
with col2:
    exam_diff_label = st.selectbox("Mức độ", ["Chưa rõ"] + [DIFFICULTY_LABELS.get(d, d) for d in DIFFICULTIES])
    exam_type_label = st.selectbox("Loại đề", ["Chưa rõ"] + [QUESTION_TYPE_LABELS.get(t, t) for t in QUESTION_TYPES])

auto_classify = st.checkbox("🤖 Tự động phân loại bằng AI", value=True)

if st.button("🚀 Upload & Xử lý", type="primary", use_container_width=True):
    if not exam_title:
        st.error("Vui lòng nhập tên đề thi!")
    elif file_bytes is None and not raw_text:
        st.error("Vui lòng upload file hoặc nhập nội dung đề thi vào Tab nhập trực tiếp!")
    else:
        with st.spinner("Hệ thống đang trích xuất câu hỏi..."):
            try:
                questions = []
                if file_bytes is not None:
                    from backend.extractors import extract_from_file
                    questions = extract_from_file(file_bytes=file_bytes, file_name=file_name)
                elif raw_text:
                    from backend.core.text_processor import TextProcessor
                    processor = TextProcessor()
                    questions = processor.extract_questions(raw_text=raw_text)

                if not questions:
                    st.warning("Không tìm thấy câu hỏi nào chuẩn định dạng trong nội dung được cung cấp.")
                else:
                    st.success(f"Trích xuất thành công {len(questions)} câu hỏi.")
                    st.session_state.upload_questions = questions

                    final_subject = exam_subject
                    final_diff = next((k for k, v in DIFFICULTY_LABELS.items() if v == exam_diff_label), None)

                    if auto_classify:
                        with st.spinner("AI đang đánh giá phân loại..."):
                            from backend.core.classifier import ExamClassifier
                            classifier = ExamClassifier()
                            classification = classifier.classify(questions=questions)

                            if exam_subject == "Chưa rõ" and "subject" in classification:
                                final_subject = classification["subject"]
                            if exam_diff_label == "Chưa rõ" and "difficulty" in classification:
                                final_diff = classification["difficulty"]

                            st.info(
                                f"**🤖 Kết quả phân loại AI (Độ tin cậy: {classification.get('confidence', 0) * 100:.1f}%):**\n"
                                f"- Môn học: {classification.get('subject')}\n"
                                f"- Mức độ: {DIFFICULTY_LABELS.get(classification.get('difficulty'), 'N/A')}\n"
                                f"- Loại đề: {QUESTION_TYPE_LABELS.get(classification.get('question_type'), 'N/A')}")

                    st.session_state.temp_exam_info = {
                        "title": exam_title,
                        "subject": final_subject if final_subject != "Chưa rõ" else SUBJECTS[0],
                        "difficulty": final_diff if final_diff else DIFFICULTIES[0],
                        "source_file": file_name if file_bytes else "Nhập trực tiếp"
                    }

            except Exception as e:
                st.error(f"Đã xảy ra lỗi khi xử lý: {e}")

if st.session_state.upload_questions:
    with st.expander("👁️ Xem trước câu hỏi trích xuất", expanded=True):
        for i, q in enumerate(st.session_state.upload_questions, 1):
            st.markdown(f"**Câu {i}:** {q.content}")
            if q.options:
                for opt in q.options:
                    st.markdown(f"- {opt}")
            st.divider()

    if st.button("💾 Lưu vào Kho Đề", type="primary", use_container_width=True):
        with st.spinner("Đang lưu đề thi vào CSDL..."):
            try:
                from backend.database.mysql_store import MySQLExamStore
                from backend.schemas.exam import Exam
                store = MySQLExamStore()
                info = st.session_state.temp_exam_info
                new_exam = Exam(
                    id=str(uuid.uuid4()),
                    title=info["title"],
                    subject=info["subject"],
                    difficulty=info["difficulty"],
                    questions=st.session_state.upload_questions,
                    source_file=info["source_file"],
                    created_at=datetime.utcnow().isoformat() + "Z"
                )
                exam_id = store.save(exam=new_exam)
                st.success(f"Đã lưu thành công đề thi (ID: {exam_id})")
                st.session_state.upload_questions = []
                st.session_state.temp_exam_info = {}
                st.session_state.voice_input_text = ""
            except Exception as e:
                st.error(f"Lỗi khi lưu vào Kho đề: {e}")
