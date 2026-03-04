import html
import re
import time
import uuid
from typing import List, Optional, Dict
from datetime import datetime

import requests

from backend.schemas.exam import Exam, Question, SearchResult
from backend.services.question_bank import get_questions
from backend.database.mysql_store import MySQLExamStore
from config import (
    CRAWLER_REQUEST_TIMEOUT, WEB_SEARCH_MAX_URLS,
    GEMINI_ENABLED, GEMINI_MIN_LOCAL_THRESHOLD,
    GROQ_ENABLED,
)


# ── OpenTDB config ──────────────────────────────────────────────
QUERY_TO_OPENTDB: List[tuple] = [
    (["python", "programming", "code", "software"], 18, "Python"),
    (["machine learning", "ml"], 18, "Machine Learning"),
    (["deep learning", "neural network", "cnn", "rnn"], 18, "Deep Learning"),
    (["nlp", "natural language"], 18, "NLP"),
    (["data science", "data analysis"], 18, "Data Science"),
    (["ai", "artificial intelligence"], 18, "Machine Learning"),
    (["computer", "database", "sql", "network"], 18, "Python"),
    (["math", "mathematics", "algebra", "calculus"], 19, None),
    (["science", "physics", "chemistry", "biology"], 17, None),
    (["history"], 23, None),
    (["geography"], 22, None),
    (["sports", "football", "tennis", "basketball"], 21, None),
    (["film", "movie", "cinema"], 11, None),
    (["music"], 12, None),
    (["book", "literature"], 10, None),
    (["game", "video game"], 15, None),
    (["animal"], 27, None),
    (["art"], 25, None),
    (["politics"], 24, None),
    (["mythology"], 20, None),
    (["vehicle", "car"], 28, None),
    (["anime", "manga"], 31, None),
    (["general", "trivia", "quiz"], 9, None),
]

# Vietnamese query → subject mapping (cho đề Việt trong kho local)
VI_QUERY_TO_SUBJECT: List[tuple] = [
    (["toan", "toán", "toan hoc", "toán học", "dai so", "đại số", "giai tich", "giải tích", "hinh hoc", "hình học"], "Toán học"),
    (["vat ly", "vật lý", "vat li", "vật lí", "ly", "lý", "dien tu", "điện từ", "co hoc", "cơ học", "quang hoc", "quang học"], "Vật lý"),
    (["hoa hoc", "hóa học", "hoa", "hóa", "hữu cơ", "huu co", "vô cơ", "vo co"], "Hóa học"),
    (["sinh hoc", "sinh học", "sinh", "di truyen", "di truyền", "te bao", "tế bào"], "Sinh học"),
    (["lich su", "lịch sử", "su", "sử", "lich su viet nam", "lịch sử việt nam"], "Lịch sử"),
    (["dia ly", "địa lý", "dia li", "địa lí", "dia", "địa", "dia ly viet nam"], "Địa lý"),
    (["tieng anh", "tiếng anh", "anh", "english", "ngu phap", "ngữ pháp", "grammar", "vocabulary"], "Tiếng Anh"),
    (["ngu van", "ngữ văn", "van hoc", "văn học", "van", "văn", "tho", "thơ"], "Ngữ văn"),
    (["tin hoc", "tin học", "tin", "lap trinh", "lập trình", "python", "programming"], "Tin học"),
    (["gdcd", "giao duc cong dan", "giáo dục công dân", "kinh te", "kinh tế", "phap luat", "pháp luật"], "GDCD"),
    (["the duc", "thể dục", "the thao", "thể thao", "bong da", "bóng đá"], "Thể dục"),
    (["cong nghe", "công nghệ"], "Công nghệ"),
    (["am nhac", "âm nhạc", "nhac", "nhạc"], "Âm nhạc"),
    (["phim", "dien anh", "điện ảnh", "movie"], "Phim"),
    (["dong vat", "động vật", "thu vat", "thú vật"], "Động vật"),
    (["nghe thuat", "nghệ thuật", "hoi hoa", "hội họa"], "Nghệ thuật"),
    (["machine learning", "hoc may", "học máy", "ml"], "Machine Learning"),
    (["deep learning"], "Deep Learning"),
    (["nlp", "xu ly ngon ngu", "xử lý ngôn ngữ"], "NLP"),
    (["data science", "khoa hoc du lieu", "khoa học dữ liệu"], "Data Science"),
    (["kien thuc chung", "kiến thức chung", "tong hop", "tổng hợp"], "Kiến thức chung"),
]

CATEGORY_DISPLAY_NAMES = {
    9: "General Knowledge", 10: "Books & Literature", 11: "Film & Cinema",
    12: "Music", 15: "Video Games", 17: "Science & Nature",
    18: "Computer Science", 19: "Mathematics", 20: "Mythology",
    21: "Sports", 22: "Geography", 23: "History",
    24: "Politics", 25: "Art", 27: "Animals",
    28: "Vehicles", 30: "Gadgets", 31: "Anime & Manga",
}

DIFF_EN = {"co_ban": "easy", "trung_binh": "medium", "nang_cao": "hard"}
DIFF_VI = {"easy": "co_ban", "medium": "trung_binh", "hard": "nang_cao"}
DIFF_LABELS_EN = {"easy": "Easy", "medium": "Medium", "hard": "Hard"}


def _is_vietnamese_query(query: str) -> bool:
    """Detect xem query có phải tiếng Việt không."""
    vi_markers = [
        "toan", "toán", "vat ly", "vật lý", "hoa hoc", "hóa học", "hoa", "hóa",
        "sinh", "lich su", "lịch sử", "dia ly", "địa lý", "dia", "địa",
        "tieng anh", "tiếng anh", "ngu van", "ngữ văn", "tin hoc", "tin học",
        "gdcd", "the thao", "thể thao", "am nhac", "âm nhạc",
        "van hoc", "văn học", "van", "văn", "tho", "thơ",
        "sinh hoc", "sinh học", "te bao", "tế bào", "di truyen", "di truyền",
        "de thi", "đề thi", "trac nghiem", "trắc nghiệm", "cau hoi", "câu hỏi",
        "bai tap", "bài tập", "kiem tra", "kiểm tra", "hoc", "học",
        "kien thuc", "kiến thức", "dong vat", "động vật", "nghe thuat", "nghệ thuật",
        "hoc may", "học máy", "khoa hoc", "khoa học", "phim", "nhac", "nhạc",
        "lap trinh", "lập trình", "co ban", "cơ bản", "nang cao", "nâng cao",
        "lop", "lớp", "su", "sử", "ly", "lý", "anh", "tin",
        "the duc", "thể dục", "cong nghe", "công nghệ",
    ]
    q = query.lower()
    return any(marker in q for marker in vi_markers)


class WebSearchService:
    """Tìm kiếm đề thi trên web.

    - Query tiếng Việt → tìm đề tiếng Việt từ kho đề mở rộng (sample data)
    - Query tiếng Anh → tìm đề tiếng Anh từ OpenTDB API
    - Giữ nguyên ngôn ngữ gốc, KHÔNG dịch máy
    """

    def __init__(self):
        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        })

    def search_web(
        self,
        query: str,
        subject: Optional[str] = None,
        difficulty: Optional[str] = None,
        grade: Optional[int] = None,
        max_results: int = WEB_SEARCH_MAX_URLS,
    ) -> List[SearchResult]:
        """Tìm đề thi: tiếng Việt → đề Việt, tiếng Anh → OpenTDB."""
        results = []

        if _is_vietnamese_query(query):
            vi_results = self._search_vietnamese(query, subject, difficulty, grade)
            results.extend(vi_results)
        else:
            en_results = self._search_opentdb(query, subject, difficulty)
            results.extend(en_results)

        results.sort(key=lambda r: (len(r.exam.questions), r.score), reverse=True)
        return results[:max_results]

    # ── Vietnamese search ────────────────────────────────────────

    def _search_vietnamese(
        self, query: str, subject: Optional[str],
        difficulty: Optional[str], grade: Optional[int],
    ) -> List[SearchResult]:
        """Tìm đề tiếng Việt từ ngân hàng câu hỏi + kho đề."""
        detected_subject = self._detect_vi_subject(query, subject)
        detected_grade = self._detect_vi_grade(query, grade)

        # 1) Kết quả từ ngân hàng câu hỏi — gộp thành 1 đề
        all_bank_qs = get_questions(
            detected_subject, grade=detected_grade, difficulty=difficulty,
        )

        results = []
        if all_bank_qs:
            grade_text = f" - Lớp {detected_grade}" if detected_grade else ""
            exam = Exam(
                id=f"vi-{uuid.uuid4().hex[:8]}",
                title=f"{detected_subject}{grade_text} ({len(all_bank_qs)} câu)",
                subject=detected_subject,
                difficulty=difficulty or "trung_binh",
                questions=all_bank_qs,
                source_file="Ngân hàng đề Việt Nam (QuizHunter)",
                created_at=datetime.utcnow().isoformat() + "Z",
                grade=detected_grade,
            )
            score = min(1.0, len(all_bank_qs) / 10.0) * 0.85
            results.append(SearchResult(
                exam=exam, score=round(score, 3), matched_questions=all_bank_qs[:3],
            ))

        # 2) Kết quả từ kho đề — bỏ đề gốc question bank
        store_results = self._search_exam_store(
            detected_subject, difficulty, detected_grade, query,
        )
        results.extend(store_results)

        # 3) MySQL FULLTEXT search — tìm theo nội dung câu hỏi
        ft_results = self._search_mysql_fulltext(
            query, detected_subject, detected_grade, difficulty,
        )
        results.extend(ft_results)

        # 4) AI sinh thêm câu nếu local quá ít (Gemini → Groq fallback)
        #    Đếm câu hỏi DUY NHẤT (tránh trùng giữa bank/store/fulltext)
        if detected_grade:
            seen_ids = set()
            for r in results:
                for q in r.exam.questions:
                    seen_ids.add(q.id)
            unique_count = len(seen_ids)

            if unique_count < GEMINI_MIN_LOCAL_THRESHOLD:
                num_to_gen = max(10, GEMINI_MIN_LOCAL_THRESHOLD - unique_count + 10)
                ai_results = self._generate_ai_questions(
                    detected_subject, detected_grade, difficulty, query,
                    num_questions=num_to_gen,
                )
                results.extend(ai_results)

        # 5) Gộp các đề nhỏ thành 1 đề lớn (nếu có nhiều đề < 10 câu)
        results = self._merge_small_results(results, detected_subject, detected_grade, difficulty)

        return results

    def _generate_ai_questions(
        self, subject: str, grade: int,
        difficulty: Optional[str], query: str,
        num_questions: int = 15,
    ) -> List[SearchResult]:
        """Thử Gemini trước, nếu lỗi thì dùng Groq."""
        if GEMINI_ENABLED:
            result = self._generate_gemini(subject, grade, difficulty, query, num_questions)
            if result:
                return result

        if GROQ_ENABLED:
            result = self._generate_groq(subject, grade, difficulty, query, num_questions)
            if result:
                return result

        return []

    def _generate_gemini(
        self, subject: str, grade: int,
        difficulty: Optional[str], query: str,
        num_questions: int = 15,
    ) -> List[SearchResult]:
        """Sinh câu hỏi bằng Gemini AI."""
        try:
            from backend.services.gemini_service import generate_questions
        except ImportError:
            return []

        topic_hint = self._clean_query_for_fulltext(query)
        qs = generate_questions(
            subject=subject, grade=grade,
            topic=topic_hint if topic_hint else None,
            difficulty=difficulty or "trung_binh",
            num_questions=num_questions,
        )
        if not qs:
            return []

        grade_text = f" - Lớp {grade}" if grade else ""
        exam = Exam(
            id=f"gemini-{uuid.uuid4().hex[:8]}",
            title=f"AI tạo: {subject}{grade_text} ({len(qs)} câu)",
            subject=subject,
            difficulty=difficulty or "trung_binh",
            questions=qs,
            source_file="Google Gemini AI",
            created_at=datetime.utcnow().isoformat() + "Z",
            grade=grade,
        )
        return [SearchResult(exam=exam, score=0.6, matched_questions=qs[:3])]

    def _generate_groq(
        self, subject: str, grade: int,
        difficulty: Optional[str], query: str,
        num_questions: int = 15,
    ) -> List[SearchResult]:
        """Sinh câu hỏi bằng Groq API (Llama 3.3 70B)."""
        try:
            from backend.services.groq_service import generate_questions
        except ImportError:
            return []

        topic_hint = self._clean_query_for_fulltext(query)
        qs = generate_questions(
            subject=subject, grade=grade,
            topic=topic_hint if topic_hint else None,
            difficulty=difficulty or "trung_binh",
            num_questions=num_questions,
        )
        if not qs:
            return []

        grade_text = f" - Lớp {grade}" if grade else ""
        exam = Exam(
            id=f"groq-{uuid.uuid4().hex[:8]}",
            title=f"AI tạo: {subject}{grade_text} ({len(qs)} câu)",
            subject=subject,
            difficulty=difficulty or "trung_binh",
            questions=qs,
            source_file="Groq AI (Llama 3.3)",
            created_at=datetime.utcnow().isoformat() + "Z",
            grade=grade,
        )
        return [SearchResult(exam=exam, score=0.6, matched_questions=qs[:3])]

    @staticmethod
    def _merge_small_results(
        results: List[SearchResult], subject: str,
        grade: Optional[int], difficulty: Optional[str],
    ) -> List[SearchResult]:
        """Gộp các đề nhỏ (< 10 câu) cùng nguồn thành 1 đề lớn."""
        big = [r for r in results if len(r.exam.questions) >= 10]
        small = [r for r in results if len(r.exam.questions) < 10]

        if len(small) <= 1:
            return results  # Không cần gộp

        # Gộp tất cả câu hỏi từ đề nhỏ
        merged_qs = []
        seen_ids = set()
        for r in small:
            for q in r.exam.questions:
                if q.id not in seen_ids:
                    merged_qs.append(q)
                    seen_ids.add(q.id)

        if not merged_qs:
            return big

        grade_text = f" - Lớp {grade}" if grade else ""
        merged_exam = Exam(
            id=f"merged-{uuid.uuid4().hex[:8]}",
            title=f"{subject}{grade_text} - Tổng hợp ({len(merged_qs)} câu)",
            subject=subject,
            difficulty=difficulty or "trung_binh",
            questions=merged_qs,
            source_file="Tổng hợp nhiều nguồn",
            created_at=datetime.utcnow().isoformat() + "Z",
            grade=grade,
        )
        score = min(1.0, len(merged_qs) / 10.0) * 0.85
        big.append(SearchResult(
            exam=merged_exam, score=round(score, 3),
            matched_questions=merged_qs[:3],
        ))

        return big

    def _search_exam_store(
        self, subject: str, difficulty: Optional[str],
        grade: Optional[int], query: str,
    ) -> List[SearchResult]:
        """Tìm đề trong kho đề, bỏ qua đề gốc import từ question bank."""
        store = MySQLExamStore()
        exams = store.get_all_exams_unfiltered()

        q_lower = query.lower()
        results = []
        for exam in exams:
            # Bỏ đề import từ question bank (đã có ở bước 1, tránh trùng)
            if exam.source_file and exam.source_file.startswith("question_bank"):
                continue

            # Lọc theo subject (trừ "Kiến thức chung" — hiện tất cả)
            if subject != "Kiến thức chung" and exam.subject != subject:
                continue
            if difficulty and exam.difficulty != difficulty:
                continue
            if grade and exam.grade and exam.grade != grade:
                continue

            # Tính điểm phù hợp
            score = 0.5
            title_lower = exam.title.lower()
            if subject.lower() in title_lower or q_lower in title_lower:
                score = 0.7
            if grade and exam.grade == grade:
                score += 0.1

            matched = exam.questions[:3]
            results.append(SearchResult(
                exam=exam, score=round(min(score, 1.0), 3),
                matched_questions=matched,
            ))

        return results

    def _search_mysql_fulltext(
        self, query: str, subject: str,
        grade: Optional[int], difficulty: Optional[str],
    ) -> List[SearchResult]:
        """Tìm câu hỏi qua MySQL FULLTEXT, nhóm thành SearchResult."""
        clean = self._clean_query_for_fulltext(query)
        if not clean or len(clean) < 3:
            return []

        store = MySQLExamStore()
        questions = store.get_questions(
            subject=subject if subject != "Kiến thức chung" else None,
            grade=grade,
            difficulty=difficulty,
            search_text=clean,
            limit=30,
        )
        if not questions:
            return []

        grade_text = f" - Lớp {grade}" if grade else ""
        exam = Exam(
            id=f"mysql-ft-{uuid.uuid4().hex[:8]}",
            title=f"{subject}{grade_text} - Kết quả tìm kiếm ({len(questions)} câu)",
            subject=subject,
            difficulty=difficulty or "trung_binh",
            questions=questions,
            source_file="MySQL FULLTEXT Search",
            created_at=datetime.utcnow().isoformat() + "Z",
            grade=grade,
        )
        score = min(1.0, len(questions) / 15.0) * 0.9
        return [SearchResult(
            exam=exam, score=round(score, 3), matched_questions=questions[:3],
        )]

    @staticmethod
    def _clean_query_for_fulltext(query: str) -> str:
        """Loại bỏ noise từ query cho FULLTEXT."""
        q = query.lower().strip()
        q = re.sub(r'l[oớ]p\s*\d{1,2}', '', q)
        noise = [
            "de thi", "đề thi", "trac nghiem", "trắc nghiệm",
            "cau hoi", "câu hỏi", "bai tap", "bài tập",
            "kiem tra", "kiểm tra", "toan", "toán",
            "vat ly", "vật lý", "hoa hoc", "hóa học",
            "sinh hoc", "sinh học", "lich su", "lịch sử",
            "dia ly", "địa lý", "tieng anh", "tiếng anh",
            "ngu van", "ngữ văn", "tin hoc", "tin học", "gdcd",
        ]
        for n in noise:
            q = q.replace(n, '')
        return q.strip()

    @staticmethod
    def _detect_vi_grade(query: str, grade_filter: Optional[int]) -> Optional[int]:
        """Phát hiện lớp từ query: 'toán 8', 'toán lớp 12', sidebar filter."""
        # 1) Sidebar filter luôn ưu tiên
        if grade_filter is not None:
            return grade_filter

        q = query.lower().strip()

        # 2) "lớp N" / "lop N"
        m = re.search(r'l[oớ]p\s*(\d{1,2})', q)
        if m:
            g = int(m.group(1))
            if 1 <= g <= 12:
                return g

        # 3) Subject keyword + số: "toán 8", "lý 10", "hóa học 12"
        subject_kws = [
            "toan hoc", "toán học", "vat ly", "vật lý", "hoa hoc", "hóa học",
            "sinh hoc", "sinh học", "lich su", "lịch sử", "dia ly", "địa lý",
            "tieng anh", "tiếng anh", "ngu van", "ngữ văn", "tin hoc", "tin học",
            "cong nghe", "công nghệ", "the duc", "thể dục",
            "toan", "toán", "ly", "lý", "hoa", "hóa", "sinh",
            "su", "sử", "dia", "địa", "anh", "van", "văn",
            "tin", "gdcd",
        ]
        for kw in subject_kws:
            pattern = re.escape(kw) + r'\s+(\d{1,2})\b'
            m = re.search(pattern, q)
            if m:
                g = int(m.group(1))
                if 1 <= g <= 12:
                    return g

        return None

    def _detect_vi_subject(self, query: str, subject_filter: Optional[str]) -> str:
        if subject_filter:
            return subject_filter
        q = query.lower()
        for keywords, subj in VI_QUERY_TO_SUBJECT:
            for kw in keywords:
                if kw in q:
                    return subj
        return "Kiến thức chung"

    # ── OpenTDB English search ───────────────────────────────────

    def _search_opentdb(
        self, query: str, subject: Optional[str], difficulty: Optional[str],
    ) -> List[SearchResult]:
        """Tìm đề tiếng Anh từ OpenTDB API."""
        category_id, display_subject = self._detect_en_category(query, subject)
        results = []

        if difficulty:
            diff_en = DIFF_EN.get(difficulty)
            r = self._fetch_opentdb(category_id, diff_en, 25, display_subject, "multiple")
            if r:
                results.append(r)
        else:
            # Batch lớn chia theo difficulty
            split = self._fetch_opentdb_split(category_id, 50, display_subject)
            results.extend(split)

            if not results:
                for i, d in enumerate(["easy", "medium", "hard"]):
                    if i > 0:
                        time.sleep(6)
                    r = self._fetch_opentdb(category_id, d, 15, display_subject, "multiple")
                    if r:
                        results.append(r)

            # Thêm True/False
            time.sleep(6)
            tf = self._fetch_opentdb(category_id, None, 15, display_subject, "boolean")
            if tf:
                results.append(tf)

        return results

    def _detect_en_category(self, query: str, subject_filter: Optional[str]) -> tuple:
        if subject_filter:
            for kws, cat, subj in QUERY_TO_OPENTDB:
                if subj and subj.lower() == subject_filter.lower():
                    return cat, subject_filter

        q = query.lower()
        for kws, cat, subj in QUERY_TO_OPENTDB:
            for kw in kws:
                if kw in q:
                    display = subj or CATEGORY_DISPLAY_NAMES.get(cat, "General Knowledge")
                    return cat, display

        return 9, "General Knowledge"

    def _fetch_opentdb_split(
        self, category: int, amount: int, display_subject: str,
    ) -> List[SearchResult]:
        data = self._call_opentdb(category, None, amount, "multiple")
        if not data:
            return []

        groups: Dict[str, List[Question]] = {"easy": [], "medium": [], "hard": []}
        for item in data:
            d = item.get("difficulty", "medium")
            groups.get(d, groups["medium"]).append(self._parse_question(item, "multiple"))

        results = []
        for d_en, qs in groups.items():
            if not qs:
                continue
            exam = Exam(
                id=f"opentdb-{uuid.uuid4().hex[:8]}",
                title=f"{display_subject} - {DIFF_LABELS_EN[d_en]} ({len(qs)} questions)",
                subject=display_subject,
                difficulty=DIFF_VI.get(d_en, "trung_binh"),
                questions=qs,
                source_file="opentdb.com",
                created_at=datetime.utcnow().isoformat() + "Z",
            )
            score = min(1.0, len(qs) / 15.0) * 0.8
            results.append(SearchResult(exam=exam, score=round(score, 3), matched_questions=qs[:3]))

        return results

    def _fetch_opentdb(
        self, category: int, difficulty: Optional[str], amount: int,
        display_subject: str, q_type: str,
    ) -> Optional[SearchResult]:
        data = self._call_opentdb(category, difficulty, amount, q_type)
        if not data:
            return None
        qs = [self._parse_question(item, q_type) for item in data]
        d = data[0].get("difficulty", "medium")
        d_label = DIFF_LABELS_EN.get(d, d)
        t_label = "Multiple Choice" if q_type == "multiple" else "True/False"

        exam = Exam(
            id=f"opentdb-{uuid.uuid4().hex[:8]}",
            title=f"{display_subject} - {t_label} - {d_label} ({len(qs)} questions)",
            subject=display_subject,
            difficulty=DIFF_VI.get(d, "trung_binh"),
            questions=qs,
            source_file="opentdb.com",
            created_at=datetime.utcnow().isoformat() + "Z",
        )
        score = min(1.0, len(qs) / 15.0) * 0.8
        return SearchResult(exam=exam, score=round(score, 3), matched_questions=qs[:3])

    def _call_opentdb(self, category, difficulty, amount, q_type):
        params = {"amount": min(amount, 50), "category": category, "type": q_type}
        if difficulty:
            params["difficulty"] = difficulty
        try:
            resp = self._session.get("https://opentdb.com/api.php", params=params, timeout=CRAWLER_REQUEST_TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
            if data.get("response_code") != 0:
                return None
            return data.get("results")
        except Exception:
            return None

    def _parse_question(self, item: dict, q_type: str) -> Question:
        content = html.unescape(item["question"])
        correct = html.unescape(item["correct_answer"])

        if q_type == "boolean":
            options = ["A. True", "B. False"]
            answer = "A" if correct == "True" else "B"
        else:
            incorrects = [html.unescape(a) for a in item["incorrect_answers"]]
            all_ans = sorted(incorrects + [correct])
            options = []
            answer = ""
            for i, ans in enumerate(all_ans):
                letter = chr(65 + i)
                options.append(f"{letter}. {ans}")
                if ans == correct:
                    answer = letter

        return Question(
            id=str(uuid.uuid4()), content=content,
            options=options, answer=answer, question_type="trac_nghiem",
        )


