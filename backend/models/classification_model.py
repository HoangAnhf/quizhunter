from typing import List, Dict, Tuple
from collections import Counter

from backend.schemas.exam import Question
from config import SUBJECTS, DIFFICULTIES


# Từ khóa đặc trưng cho từng môn học - mở rộng với weights
# Format: (keyword, weight) - weight cao = đặc trưng hơn
SUBJECT_KEYWORDS: Dict[str, List[Tuple[str, float]]] = {
    "Machine Learning": [
        # Core concepts (high weight)
        ("machine learning", 3.0), ("học máy", 3.0),
        ("supervised learning", 2.5), ("unsupervised learning", 2.5),
        ("reinforcement learning", 2.5), ("học có giám sát", 2.5),
        ("học không giám sát", 2.5), ("học tăng cường", 2.5),
        # Algorithms
        ("regression", 2.0), ("hồi quy", 2.0),
        ("classification", 1.5), ("phân loại", 1.5),
        ("decision tree", 2.0), ("cây quyết định", 2.0),
        ("random forest", 2.0), ("rừng ngẫu nhiên", 2.0),
        ("svm", 2.0), ("support vector", 2.0),
        ("gradient descent", 2.0), ("gradient boosting", 2.0),
        ("xgboost", 2.5), ("lightgbm", 2.5), ("adaboost", 2.0),
        ("k-nearest", 2.0), ("knn", 2.0), ("naive bayes", 2.0),
        ("logistic regression", 2.0), ("linear regression", 2.0),
        ("ensemble", 1.5), ("bagging", 2.0), ("boosting", 2.0),
        # Clustering
        ("k-means", 2.0), ("dbscan", 2.0), ("clustering", 1.5),
        ("hierarchical clustering", 2.0), ("phân cụm", 2.0),
        ("silhouette", 2.0), ("elbow method", 2.0),
        # Concepts
        ("overfitting", 2.0), ("underfitting", 2.0),
        ("bias-variance", 2.5), ("cross validation", 2.0),
        ("train test split", 2.0), ("feature engineering", 1.5),
        ("feature selection", 2.0), ("regularization", 2.0),
        ("l1", 1.0), ("l2", 1.0), ("lasso", 2.0), ("ridge", 2.0),
        ("hyperparameter", 1.5), ("grid search", 2.0),
        ("precision", 1.0), ("recall", 1.0), ("f1 score", 2.0),
        ("confusion matrix", 2.0), ("roc", 1.5), ("auc", 1.5),
        ("sklearn", 2.0), ("scikit-learn", 2.5),
        # Vietnamese
        ("huấn luyện", 1.0), ("kiểm thử", 1.0), ("mô hình", 1.0),
        ("đặc trưng", 1.0), ("dự đoán", 1.0), ("tập dữ liệu", 1.0),
        ("quá khớp", 2.0), ("chưa khớp", 2.0),
    ],
    "NLP": [
        # Core (high weight)
        ("nlp", 3.0), ("natural language processing", 3.0),
        ("xử lý ngôn ngữ", 3.0), ("ngôn ngữ tự nhiên", 3.0),
        # Techniques
        ("tokenize", 2.0), ("tokenization", 2.0), ("tách từ", 2.0),
        ("stemming", 2.0), ("lemmatization", 2.0),
        ("embedding", 1.5), ("word2vec", 2.5), ("glove", 2.5),
        ("word embedding", 2.5), ("fasttext", 2.5),
        ("bag of words", 2.0), ("tf-idf", 2.5), ("tfidf", 2.5),
        ("stop words", 2.0), ("n-gram", 2.0), ("bigram", 2.0),
        ("pos tagging", 2.5), ("gán nhãn từ loại", 2.5),
        # Models
        ("bert", 2.5), ("gpt", 2.5), ("transformer", 2.0),
        ("attention mechanism", 2.0), ("self-attention", 2.5),
        ("seq2seq", 2.5), ("encoder decoder", 2.0),
        ("language model", 2.0), ("mô hình ngôn ngữ", 2.0),
        ("fine-tuning", 1.5), ("pre-training", 1.5),
        ("beam search", 2.0), ("perplexity", 2.5),
        # Tasks
        ("sentiment", 2.0), ("phân tích cảm xúc", 2.5),
        ("ner", 2.0), ("named entity", 2.5), ("nhận dạng thực thể", 2.5),
        ("text classification", 2.0), ("phân loại văn bản", 2.5),
        ("machine translation", 2.0), ("dịch máy", 2.5),
        ("question answering", 2.0), ("chatbot", 1.5),
        ("text generation", 2.0), ("sinh văn bản", 2.0),
        ("summarization", 2.0), ("tóm tắt văn bản", 2.0),
        ("information retrieval", 2.0), ("truy xuất thông tin", 2.0),
    ],
    "Deep Learning": [
        # Core (high weight)
        ("deep learning", 3.0), ("học sâu", 3.0),
        ("neural network", 2.5), ("mạng nơ-ron", 2.5), ("mạng nơron", 2.5),
        # Architecture
        ("cnn", 2.0), ("convolutional", 2.0), ("convolution", 2.0),
        ("rnn", 2.0), ("recurrent", 2.0),
        ("lstm", 2.5), ("gru", 2.5),
        ("resnet", 2.5), ("vgg", 2.5), ("inception", 2.0),
        ("unet", 2.5), ("yolo", 2.5),
        ("gan", 2.5), ("generative adversarial", 2.5),
        ("autoencoder", 2.5), ("vae", 2.5),
        # Concepts
        ("backpropagation", 2.5), ("lan truyền ngược", 2.5),
        ("activation", 1.5), ("hàm kích hoạt", 2.0),
        ("relu", 2.0), ("sigmoid", 1.5), ("softmax", 1.5), ("tanh", 1.5),
        ("dropout", 2.0), ("batch normalization", 2.5),
        ("pooling", 2.0), ("max pooling", 2.0),
        ("epoch", 1.5), ("batch size", 1.5),
        ("layer", 1.0), ("tầng", 1.0),
        ("neuron", 1.5), ("nơ-ron", 1.5), ("perceptron", 2.0),
        ("loss function", 1.5), ("hàm mất mát", 2.0),
        ("optimizer", 1.5), ("adam", 1.5), ("sgd", 1.5),
        ("learning rate", 1.5), ("tốc độ học", 1.5),
        ("vanishing gradient", 2.5), ("exploding gradient", 2.5),
        ("transfer learning", 2.0), ("học chuyển giao", 2.0),
        ("data augmentation", 2.0), ("tăng cường dữ liệu", 2.0),
        # Tasks
        ("image classification", 2.0), ("phân loại ảnh", 2.0),
        ("object detection", 2.5), ("phát hiện vật thể", 2.5),
        ("semantic segmentation", 2.5), ("phân đoạn ngữ nghĩa", 2.5),
        ("computer vision", 2.0), ("thị giác máy tính", 2.0),
        # Frameworks
        ("pytorch", 2.0), ("tensorflow", 2.0), ("keras", 2.0),
    ],
    "Python": [
        # Core (high weight)
        ("python", 3.0),
        # Syntax
        ("def ", 1.5), ("class ", 1.5), ("import ", 1.0),
        ("list", 1.0), ("dict", 1.0), ("tuple", 1.5), ("set", 1.0),
        ("for loop", 1.5), ("while loop", 1.5), ("vòng lặp", 1.5),
        ("if else", 1.0), ("try except", 1.5),
        ("lambda", 2.0), ("decorator", 2.5), ("generator", 2.5),
        ("comprehension", 2.0), ("list comprehension", 2.5),
        ("context manager", 2.5), ("with statement", 2.0),
        # OOP
        ("inheritance", 1.5), ("kế thừa", 1.5),
        ("polymorphism", 2.0), ("đa hình", 2.0),
        ("encapsulation", 2.0), ("đóng gói", 1.5),
        ("abstract class", 2.0), ("lớp trừu tượng", 2.0),
        ("__init__", 2.0), ("self.", 1.0), ("__str__", 2.0),
        # Advanced
        ("metaclass", 2.5), ("descriptor", 2.5),
        ("async", 2.0), ("await", 2.0), ("asyncio", 2.5),
        ("threading", 2.0), ("multiprocessing", 2.0),
        ("gil", 2.5), ("global interpreter lock", 2.5),
        ("memory management", 1.5), ("garbage collection", 2.0),
        ("design pattern", 2.0), ("mẫu thiết kế", 2.0),
        # Libraries & tools
        ("pip", 1.5), ("virtualenv", 2.0), ("venv", 1.5),
        ("flask", 2.0), ("fastapi", 2.0), ("django", 2.0),
        ("rest api", 1.5), ("http", 1.0), ("json", 1.0),
        # Data structures
        ("stack", 1.5), ("queue", 1.5), ("linked list", 2.0),
        ("binary search", 1.5), ("sorting", 1.0),
        # Vietnamese
        ("hàm", 1.0), ("biến", 1.0), ("danh sách", 1.0),
        ("từ điển", 1.5), ("kiểu dữ liệu", 1.0),
        ("chuỗi", 1.0), ("mảng", 1.0),
    ],
    "Data Science": [
        # Core (high weight)
        ("data science", 3.0), ("khoa học dữ liệu", 3.0),
        # Libraries
        ("pandas", 2.5), ("numpy", 2.0), ("matplotlib", 2.5),
        ("seaborn", 2.5), ("plotly", 2.0), ("scipy", 2.0),
        ("dataframe", 2.5), ("series", 1.5),
        # Operations
        ("groupby", 2.0), ("merge", 1.5), ("join", 1.5),
        ("pivot table", 2.5), ("pivot_table", 2.5),
        ("describe()", 2.0), ("info()", 1.5),
        ("fillna", 2.0), ("dropna", 2.0), ("missing value", 2.0),
        ("giá trị thiếu", 2.0), ("dữ liệu bị thiếu", 2.0),
        # Statistics
        ("statistics", 1.5), ("thống kê", 2.0),
        ("mean", 1.0), ("median", 1.5), ("mode", 1.0),
        ("standard deviation", 2.0), ("độ lệch chuẩn", 2.5),
        ("variance", 1.5), ("phương sai", 2.0),
        ("correlation", 2.0), ("tương quan", 2.0),
        ("normal distribution", 2.0), ("phân phối chuẩn", 2.5),
        ("probability", 1.5), ("xác suất", 1.5),
        ("hypothesis testing", 2.5), ("kiểm định giả thuyết", 2.5),
        ("p-value", 2.5), ("confidence interval", 2.0),
        ("bayes", 1.5), ("bayesian", 1.5),
        # Techniques
        ("eda", 2.5), ("exploratory data analysis", 2.5),
        ("feature engineering", 2.0), ("data cleaning", 2.0),
        ("data pipeline", 2.0), ("etl", 2.0),
        ("a/b testing", 2.5), ("ab testing", 2.5),
        ("time series", 2.5), ("chuỗi thời gian", 2.5),
        ("pca", 2.5), ("dimensionality reduction", 2.5),
        ("anomaly detection", 2.0), ("phát hiện bất thường", 2.5),
        # Visualization
        ("visualization", 2.0), ("trực quan hóa", 2.5),
        ("biểu đồ", 1.5), ("chart", 1.0), ("plot", 1.0),
        ("histogram", 2.0), ("scatter plot", 2.0), ("heatmap", 2.0),
        # Data
        ("csv", 1.5), ("dataset", 1.0), ("tập dữ liệu", 1.5),
        ("big data", 2.0), ("dữ liệu lớn", 2.0),
        ("data ethics", 2.0), ("đạo đức dữ liệu", 2.5),
    ],
}

# Từ khóa cho mức độ khó - mở rộng
DIFFICULTY_KEYWORDS: Dict[str, List[Tuple[str, float]]] = {
    "co_ban": [
        # Definitions
        ("là gì", 2.0), ("what is", 2.0), ("define", 2.0),
        ("định nghĩa", 2.0), ("khái niệm", 1.5),
        # Simple tasks
        ("liệt kê", 1.5), ("list", 1.0), ("nêu", 1.5), ("kể tên", 1.5),
        ("basic", 1.5), ("cơ bản", 2.0), ("đơn giản", 1.5), ("simple", 1.5),
        ("true or false", 2.0), ("đúng hay sai", 2.0),
        ("chọn đáp án đúng", 1.5), ("chọn câu đúng", 1.5),
        # Recognition
        ("nhận biết", 1.5), ("identify", 1.5), ("recognize", 1.5),
        ("nêu tên", 1.5), ("ý nào sau đây", 1.0),
        ("câu nào đúng", 1.5), ("câu nào sai", 1.5),
        ("cho biết", 1.5), ("nêu ý nghĩa", 1.5),
    ],
    "trung_binh": [
        # Comparison
        ("so sánh", 2.0), ("compare", 2.0), ("khác nhau", 1.5),
        ("giống nhau", 1.5), ("difference", 1.5),
        # Explanation
        ("explain", 2.0), ("giải thích", 2.0), ("tại sao", 2.0),
        ("why", 1.5), ("how", 1.0), ("làm thế nào", 1.5),
        ("như thế nào", 1.5),
        # Application
        ("ví dụ", 1.5), ("example", 1.5), ("cho ví dụ", 2.0),
        ("phân biệt", 2.0), ("distinguish", 2.0),
        ("trình bày", 1.5), ("describe", 1.5),
        ("áp dụng", 2.0), ("apply", 2.0), ("ứng dụng", 1.5),
        # Analysis
        ("phân tích", 1.5), ("tính toán", 1.5), ("calculate", 1.5),
        ("viết chương trình", 1.5), ("implement", 1.5),
        ("xây dựng", 1.5), ("thực hiện", 1.0),
    ],
    "nang_cao": [
        # Deep analysis
        ("chứng minh", 2.5), ("prove", 2.5),
        ("thiết kế", 2.0), ("design", 2.0),
        ("tối ưu", 2.0), ("optimize", 2.0), ("optimization", 2.0),
        ("đánh giá", 1.5), ("evaluate", 1.5), ("evaluation", 1.5),
        # Complex tasks
        ("advanced", 2.0), ("nâng cao", 2.0),
        ("complex", 1.5), ("phức tạp", 1.5),
        ("research", 2.0), ("nghiên cứu", 2.0),
        ("propose", 2.0), ("đề xuất", 2.0),
        # Critical thinking
        ("so sánh ưu nhược điểm", 2.5), ("trade-off", 2.0),
        ("đánh giá hiệu quả", 2.0), ("phản biện", 2.0),
        ("cải tiến", 2.0), ("improve", 1.5),
        ("hạn chế", 1.5), ("limitation", 1.5),
        ("giải pháp", 1.5), ("solution", 1.0),
        ("kiến trúc", 2.0), ("architecture", 2.0),
        ("scalability", 2.0), ("khả năng mở rộng", 2.0),
    ],
}

# N-gram patterns cho phân loại chính xác hơn
SUBJECT_NGRAMS: Dict[str, List[Tuple[str, float]]] = {
    "Machine Learning": [
        ("train test split", 3.0), ("cross validation", 3.0),
        ("gradient descent algorithm", 3.0), ("hàm mất mát", 3.0),
        ("tập huấn luyện", 3.0), ("feature importance", 3.0),
    ],
    "NLP": [
        ("natural language processing", 3.5),
        ("xử lý ngôn ngữ tự nhiên", 3.5),
        ("named entity recognition", 3.0),
        ("text classification", 3.0),
        ("sentiment analysis", 3.0),
        ("attention mechanism", 3.0),
    ],
    "Deep Learning": [
        ("neural network architecture", 3.5),
        ("convolutional neural network", 3.5),
        ("recurrent neural network", 3.5),
        ("generative adversarial network", 3.5),
        ("batch normalization layer", 3.0),
        ("vanishing gradient problem", 3.0),
    ],
    "Python": [
        ("list comprehension", 3.0),
        ("exception handling", 3.0),
        ("object oriented programming", 3.0),
        ("lập trình hướng đối tượng", 3.0),
        ("global interpreter lock", 3.0),
    ],
    "Data Science": [
        ("exploratory data analysis", 3.5),
        ("khoa học dữ liệu", 3.5),
        ("hypothesis testing", 3.0),
        ("standard deviation", 3.0),
        ("confidence interval", 3.0),
        ("data visualization", 3.0),
    ],
}


class ClassificationModel:
    """Phân loại đề thi dựa trên từ khóa đặc trưng với weighted scoring."""

    def predict_subject(self, text: str) -> tuple:
        text_lower = text.lower()
        scores = {}

        for subject, keywords in SUBJECT_KEYWORDS.items():
            score = 0.0
            for kw, weight in keywords:
                if kw in text_lower:
                    # Đếm số lần xuất hiện, nhưng cap ở 3 lần
                    count = min(text_lower.count(kw), 3)
                    score += weight * count
            scores[subject] = score

        # Thêm n-gram scoring
        for subject, ngrams in SUBJECT_NGRAMS.items():
            for ngram, weight in ngrams:
                if ngram in text_lower:
                    count = min(text_lower.count(ngram), 2)
                    scores[subject] = scores.get(subject, 0) + weight * count

        if not scores or max(scores.values()) == 0:
            return SUBJECTS[0], 0.0

        best = max(scores, key=scores.get)
        total = sum(scores.values())
        confidence = scores[best] / total if total > 0 else 0.0
        return best, min(confidence, 1.0)

    def predict_difficulty(self, text: str) -> tuple:
        text_lower = text.lower()
        scores = {}

        for diff, keywords in DIFFICULTY_KEYWORDS.items():
            score = 0.0
            for kw, weight in keywords:
                if kw in text_lower:
                    count = min(text_lower.count(kw), 3)
                    score += weight * count
            scores[diff] = score

        if not scores or max(scores.values()) == 0:
            return DIFFICULTIES[0], 0.0

        best = max(scores, key=scores.get)
        total = sum(scores.values())
        confidence = scores[best] / total if total > 0 else 0.0
        return best, min(confidence, 1.0)

    def predict_question_type(self, questions: List[Question]) -> str:
        types = Counter(q.question_type for q in questions)
        if not types:
            return "trac_nghiem"
        return types.most_common(1)[0][0]
