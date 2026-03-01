import streamlit as st
import sys
from pathlib import Path

root_path = Path(__file__).parent.parent.parent
if str(root_path) not in sys.path:
    sys.path.append(str(root_path))

from frontend.utils.ui_helpers import load_css

st.set_page_config(page_title="Giới thiệu", page_icon="ℹ️", layout="wide")
load_css()

st.title("ℹ️ Giới thiệu QuizHunter")
st.write("---")

st.markdown("""
### 🎓 Về dự án
**QuizHunter** là ứng dụng Trợ lý AI giúp sinh viên và giảng viên tìm kiếm, upload, quản lý và phân tích các đề thi một cách thông minh. Bằng việc tận dụng sức mạnh của trí tuệ nhân tạo, ứng dụng có thể tự động trích xuất cấu trúc câu hỏi, phân loại mức độ môn học và tra cứu ngữ nghĩa các câu hỏi cực kì nhanh chóng và độ chính xác cao.

### 🛠️ Công nghệ sử dụng
- **Frontend:** Streamlit, Custom CSS Animations mượt mà
- **AI/ML:** Mô hình Embeddings NLP (Sentence-Transformers), Khai phá dữ liệu Vector với FAISS
- **Machine Learning:** Phân loại tự động văn bản với Scikit-Learn
- **Processing:** PyPDF2 / Python-docx

### 📖 Hướng dẫn sử dụng
1. **🔍 Tìm kiếm nhanh:** Sử dụng thanh tìm kiếm ở Trang Chủ hoặc Tab Tìm Kiếm để tìm các câu hỏi bằng ngôn ngữ tự nhiên. 
2. **📤 Upload đề thi:** Tải lên các tệp bài thi (PDF/DOCX/TXT). AI sẽ tự động phân tách đề thi, trích xuất câu hỏi và phân loại mức độ khó.
3. **📚 Quản lý kho đề:** Theo dõi tất cả đề thi tại trang Kho Đề. Tại đây bạn có thể mở xem trực tiếp câu hỏi đáp án trên giao diện hoặc Tải xuống dạng văn bản Text để dễ dàng in ấn.

### 👤 Thông tin liên hệ
- **Tác giả:** QuizHunter Developer Team
- **GitHub Repo:** [https://github.com/quizhunter/quizhunter-app](#)
- **Email Hỗ trợ:** contact@quizhunter.edu.vn
""")