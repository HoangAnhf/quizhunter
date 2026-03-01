import os
from pathlib import Path

BASE_DIR = Path(__file__).parent

# Subjects
SUBJECTS = ["Machine Learning", "NLP", "Deep Learning", "Python", "Data Science"]

# Difficulties
DIFFICULTIES = ["co_ban", "trung_binh", "nang_cao"]

# Question types
QUESTION_TYPES = ["trac_nghiem", "tu_luan", "bai_tap"]

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
