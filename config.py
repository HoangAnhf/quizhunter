import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")

# Subjects (gốc — giữ cho backward-compatible với exam đã lưu)
SUBJECTS = ["Machine Learning", "NLP", "Deep Learning", "Python", "Data Science"]

# 12 môn phổ thông Việt Nam
VI_SUBJECTS = [
    "Toán học", "Vật lý", "Hóa học", "Sinh học",
    "Lịch sử", "Địa lý", "Tiếng Anh", "Ngữ văn",
    "Tin học", "GDCD", "Công nghệ", "Thể dục",
]

# Mapping subject display name → JSON filename
VI_SUBJECT_FILES = {
    "Toán học": "toan.json",
    "Vật lý": "vat_ly.json",
    "Hóa học": "hoa_hoc.json",
    "Sinh học": "sinh_hoc.json",
    "Lịch sử": "lich_su.json",
    "Địa lý": "dia_ly.json",
    "Tiếng Anh": "tieng_anh.json",
    "Ngữ văn": "ngu_van.json",
    "Tin học": "tin_hoc.json",
    "GDCD": "gdcd.json",
    "Công nghệ": "cong_nghe.json",
    "Thể dục": "the_duc.json",
}

# Subject short codes for exam code generation (VD: TOAN-8-CB-001)
VI_SUBJECT_CODES = {
    "Toán học": "TOAN", "Vật lý": "LY", "Hóa học": "HOA", "Sinh học": "SINH",
    "Lịch sử": "SU", "Địa lý": "DIA", "Tiếng Anh": "ANH", "Ngữ văn": "VAN",
    "Tin học": "TIN", "GDCD": "GDCD", "Công nghệ": "CN", "Thể dục": "TD",
    "Machine Learning": "ML", "NLP": "NLP", "Deep Learning": "DL",
    "Python": "PY", "Data Science": "DS",
}

# Difficulty short codes for exam code
DIFFICULTY_CODES = {
    "co_ban": "CB", "trung_binh": "TB", "nang_cao": "NC", "hon_hop": "HH",
}

# Tất cả subjects (gốc + VN) cho dropdown
ALL_SUBJECTS = SUBJECTS + VI_SUBJECTS

# Lớp 1-12
GRADES = list(range(1, 13))

# Difficulties
DIFFICULTIES = ["co_ban", "trung_binh", "nang_cao", "hon_hop"]

# Question types
QUESTION_TYPES = ["trac_nghiem", "tu_luan", "bai_tap", "noi_cot"]

# Supported file formats for upload
SUPPORTED_FORMATS = [".pdf", ".docx", ".txt"]

# Search settings
TOP_K_RESULTS = 10

# Embedding model for semantic search
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

# Data paths
DATA_DIR = BASE_DIR / "data"
FAISS_INDEX_PATH = DATA_DIR / "faiss_index" / "exam_vectors.index"
EXAM_DB_PATH = DATA_DIR / "exam_database.json"
SAMPLE_EXAMS_DIR = DATA_DIR / "sample_exams"
QUESTION_BANK_DIR = DATA_DIR / "question_bank"

# Deepgram API Configuration
DEEPGRAM_API_KEY = "f6ddf2cb03f3d132f7218b05376d3777a28c6230"
DEEPGRAM_MODEL = "nova-2"
DEEPGRAM_LANGUAGE = "vi"
DEEPGRAM_SMART_FORMAT = True
DEEPGRAM_PUNCTUATE = True

# Web Crawler Settings
CRAWLER_USER_AGENT = "QuizHunter/1.0 (Educational Research Bot)"
CRAWLER_REQUEST_TIMEOUT = 15
CRAWLER_MAX_QUESTIONS_PER_PAGE = 50

# Web Search Settings
WEB_SEARCH_MAX_URLS = 5  # Số trang web tối đa sẽ crawl mỗi lần tìm kiếm

# Gemini API (free tier)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_ENABLED = bool(GEMINI_API_KEY)
GEMINI_MIN_LOCAL_THRESHOLD = 15  # Sinh thêm câu nếu local < 15

# Groq API (free tier — Llama 3.3 70B)
GROQ_API_KEYS = [
    k for k in [
        os.getenv("GROQ_API_KEY_1", ""),
        os.getenv("GROQ_API_KEY_2", ""),
        os.getenv("GROQ_API_KEY_3", ""),
        os.getenv("GROQ_API_KEY_4", ""),
    ] if k
]
GROQ_ENABLED = bool(GROQ_API_KEYS)
GROQ_MODEL = "llama-3.3-70b-versatile"

# MySQL Database Settings
MYSQL_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "localhost"),
    "user": os.getenv("MYSQL_USER", "quizhunter"),
    "password": os.getenv("MYSQL_PASSWORD", "1234567"),
    "database": os.getenv("MYSQL_DATABASE", "quizhunter"),
    "charset": "utf8mb4",
}
