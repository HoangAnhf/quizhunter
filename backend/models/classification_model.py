from typing import List, Dict
from collections import Counter

from backend.schemas.exam import Question
from config import SUBJECTS, DIFFICULTIES


# Từ khóa đặc trưng cho từng môn học
SUBJECT_KEYWORDS: Dict[str, List[str]] = {
    "Machine Learning": [
        "machine learning", "ml", "supervised", "unsupervised", "regression",
        "classification", "decision tree", "random forest", "svm", "support vector",
        "gradient descent", "overfitting", "underfitting", "cross validation",
        "bias", "variance", "feature", "training", "testing", "model",
        "học máy", "hồi quy", "phân loại", "cây quyết định", "rừng ngẫu nhiên",
        "huấn luyện", "kiểm thử", "mô hình", "đặc trưng",
    ],
    "NLP": [
        "nlp", "natural language", "tokenize", "embedding", "word2vec",
        "bert", "transformer", "attention", "sentiment", "ner",
        "named entity", "pos tagging", "text classification", "language model",
        "xử lý ngôn ngữ", "ngôn ngữ tự nhiên", "phân tích cảm xúc",
        "mô hình ngôn ngữ", "dịch máy", "chatbot",
    ],
    "Deep Learning": [
        "deep learning", "neural network", "cnn", "rnn", "lstm", "gru",
        "convolutional", "recurrent", "backpropagation", "activation",
        "relu", "sigmoid", "softmax", "dropout", "batch normalization",
        "epoch", "layer", "neuron", "perceptron", "gan", "autoencoder",
        "học sâu", "mạng nơ-ron", "tầng", "nơ-ron", "lan truyền ngược",
    ],
    "Python": [
        "python", "def", "class", "import", "list", "dict", "tuple",
        "function", "loop", "for", "while", "if else", "try except",
        "lambda", "decorator", "generator", "comprehension", "pip",
        "variable", "string", "integer", "float", "boolean",
        "hàm", "biến", "vòng lặp", "danh sách", "từ điển",
    ],
    "Data Science": [
        "data science", "pandas", "numpy", "matplotlib", "visualization",
        "dataset", "dataframe", "csv", "statistics", "mean", "median",
        "standard deviation", "correlation", "hypothesis", "probability",
        "khoa học dữ liệu", "trực quan hóa", "thống kê", "xác suất",
        "phân phối", "tương quan", "dữ liệu",
    ],
}

# Từ khóa cho mức độ khó
DIFFICULTY_KEYWORDS: Dict[str, List[str]] = {
    "co_ban": [
        "là gì", "what is", "define", "định nghĩa", "liệt kê", "list",
        "nêu", "basic", "cơ bản", "đơn giản", "simple", "true or false",
        "đúng hay sai", "chọn đáp án đúng",
    ],
    "trung_binh": [
        "so sánh", "compare", "explain", "giải thích", "tại sao", "why",
        "how", "làm thế nào", "ví dụ", "example", "phân biệt",
        "trình bày", "describe", "áp dụng", "apply",
    ],
    "nang_cao": [
        "chứng minh", "prove", "thiết kế", "design", "implement",
        "tối ưu", "optimize", "phân tích", "analyze", "evaluate",
        "đánh giá", "advanced", "nâng cao", "complex", "phức tạp",
        "research", "nghiên cứu", "propose", "đề xuất",
    ],
}


class ClassificationModel:
    """Phân loại đề thi dựa trên từ khóa đặc trưng."""

    def predict_subject(self, text: str) -> tuple:
        text_lower = text.lower()
        scores = {}
        for subject, keywords in SUBJECT_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            scores[subject] = score

        if not scores or max(scores.values()) == 0:
            return SUBJECTS[0], 0.0

        best = max(scores, key=scores.get)
        total_keywords = sum(scores.values())
        confidence = scores[best] / total_keywords if total_keywords > 0 else 0.0
        return best, min(confidence, 1.0)

    def predict_difficulty(self, text: str) -> tuple:
        text_lower = text.lower()
        scores = {}
        for diff, keywords in DIFFICULTY_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            scores[diff] = score

        if not scores or max(scores.values()) == 0:
            return DIFFICULTIES[0], 0.0

        best = max(scores, key=scores.get)
        total_keywords = sum(scores.values())
        confidence = scores[best] / total_keywords if total_keywords > 0 else 0.0
        return best, min(confidence, 1.0)

    def predict_question_type(self, questions: List[Question]) -> str:
        types = Counter(q.question_type for q in questions)
        if not types:
            return "trac_nghiem"
        return types.most_common(1)[0][0]
