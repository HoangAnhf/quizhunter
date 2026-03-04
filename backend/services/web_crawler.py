import re
import uuid
from typing import List, Optional, Dict, Set
from urllib.parse import urlparse, urljoin

import requests
from bs4 import BeautifulSoup, Tag

from backend.schemas.exam import Question
from config import CRAWLER_USER_AGENT, CRAWLER_REQUEST_TIMEOUT, CRAWLER_MAX_QUESTIONS_PER_PAGE

# ── Chuyển đổi LaTeX → Unicode/text đọc được ──────────

_SUPERSCRIPT_MAP = str.maketrans("0123456789+-=()n", "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾ⁿ")
_SUBSCRIPT_MAP = str.maketrans("0123456789+-=()", "₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎")

_LATEX_SYMBOLS = {
    # Toán tử & quan hệ
    r"\ge": "≥", r"\geq": "≥", r"\le": "≤", r"\leq": "≤",
    r"\ne": "≠", r"\neq": "≠", r"\approx": "≈",
    r"\pm": "±", r"\mp": "∓", r"\times": "×", r"\cdot": "·", r"\div": "÷",
    r"\infty": "∞", r"\to": "→", r"\rightarrow": "→", r"\leftarrow": "←",
    r"\Rightarrow": "⇒", r"\Leftarrow": "⇐", r"\Leftrightarrow": "⇔",
    r"\in": "∈", r"\notin": "∉", r"\subset": "⊂", r"\subseteq": "⊆",
    r"\cup": "∪", r"\cap": "∩", r"\emptyset": "∅", r"\varnothing": "∅",
    r"\forall": "∀", r"\exists": "∃",
    # Hàm số
    r"\sin": "sin", r"\cos": "cos", r"\tan": "tan", r"\cot": "cot",
    r"\sec": "sec", r"\csc": "csc",
    r"\ln": "ln", r"\log": "log", r"\exp": "exp",
    r"\lim": "lim", r"\min": "min", r"\max": "max",
    # Tích phân, tổng, tích
    r"\int": "∫", r"\sum": "Σ", r"\prod": "∏",
    # Ký tự Hy Lạp thường gặp
    r"\alpha": "α", r"\beta": "β", r"\gamma": "γ", r"\delta": "δ",
    r"\epsilon": "ε", r"\theta": "θ", r"\lambda": "λ", r"\mu": "μ",
    r"\pi": "π", r"\sigma": "σ", r"\phi": "φ", r"\omega": "ω",
    r"\Delta": "Δ", r"\Sigma": "Σ", r"\Omega": "Ω", r"\Pi": "Π",
    # Tập hợp
    r"\mathbb{R}": "ℝ", r"\mathbb{N}": "ℕ", r"\mathbb{Z}": "ℤ",
    r"\mathbb{Q}": "ℚ", r"\mathbb{C}": "ℂ",
    # Khoảng cách & dấu
    r"\quad": " ", r"\qquad": "  ", r"\,": " ", r"\;": " ", r"\!": "",
    r"\ldots": "...", r"\cdots": "⋯", r"\dots": "...",
    r"\overline": "", r"\underline": "", r"\hat": "",
    r"\vec": "", r"\bar": "", r"\tilde": "",
}


def _latex_to_text(text: str) -> str:
    """Chuyển đổi LaTeX math → text Unicode đọc được.

    Ví dụ:
      \\(y = x^{2} + 3\\)  →  y = x² + 3
      \\frac{a}{b}         →  (a)/(b)
      \\sqrt{x}            →  √(x)
    """
    if not text or '\\' not in text:
        return text

    # Bỏ delimiter \( \) \[ \] $ $$ và \displaystyle
    t = text
    t = t.replace(r'\(', '').replace(r'\)', '')
    t = t.replace(r'\[', '').replace(r'\]', '')
    t = re.sub(r'\$\$?', '', t)
    t = t.replace(r'\displaystyle', '')

    # Bỏ \left \right (giữ dấu ngoặc sau nó)
    t = re.sub(r'\\left\s*', '', t)
    t = re.sub(r'\\right\s*', '', t)

    # \text{abc} → abc, \mathrm{abc} → abc, \mathop{abc} → abc
    t = re.sub(r'\\(?:text|mathrm|mathop|operatorname|mathbf|mathit)\s*\{([^}]*)\}', r'\1', t)

    # \mathbb{R} etc. (xử lý trước khi bỏ braces)
    for latex_cmd, symbol in _LATEX_SYMBOLS.items():
        if '{' in latex_cmd:
            t = t.replace(latex_cmd, symbol)

    # \frac{a}{b} → (a)/(b)
    # Xử lý nested braces đơn giản
    for _ in range(3):  # lặp để xử lý frac lồng nhau
        t = re.sub(
            r'\\(?:frac|dfrac|tfrac)\s*\{([^{}]*)\}\s*\{([^{}]*)\}',
            r'(\1)/(\2)', t
        )

    # \sqrt[n]{x} → ⁿ√(x)
    t = re.sub(
        r'\\sqrt\s*\[([^\]]*)\]\s*\{([^{}]*)\}',
        lambda m: m.group(1).translate(_SUPERSCRIPT_MAP) + '√(' + m.group(2) + ')',
        t
    )
    # \sqrt{x} → √(x)
    t = re.sub(r'\\sqrt\s*\{([^{}]*)\}', r'√(\1)', t)

    # x^{abc} → x với abc viết superscript
    def _sup(m):
        inner = m.group(1)
        # Chỉ chuyển superscript nếu ngắn (≤ 5 ký tự) và toàn số/dấu
        if len(inner) <= 5 and all(c in '0123456789+-=()n' for c in inner):
            return inner.translate(_SUPERSCRIPT_MAP)
        return '^(' + inner + ')'
    t = re.sub(r'\^\s*\{([^{}]*)\}', _sup, t)
    # x^2 (không có braces, 1 ký tự)
    t = re.sub(r'\^\s*([0-9n])', lambda m: m.group(1).translate(_SUPERSCRIPT_MAP), t)

    # x_{abc} → x với abc viết subscript
    def _sub(m):
        inner = m.group(1)
        if len(inner) <= 5 and all(c in '0123456789+-=()' for c in inner):
            return inner.translate(_SUBSCRIPT_MAP)
        return '_(' + inner + ')'
    t = re.sub(r'_\s*\{([^{}]*)\}', _sub, t)
    t = re.sub(r'_\s*([0-9])', lambda m: m.group(1).translate(_SUBSCRIPT_MAP), t)

    # Thay thế các ký hiệu LaTeX còn lại
    for latex_cmd, symbol in _LATEX_SYMBOLS.items():
        if '{' not in latex_cmd:
            t = t.replace(latex_cmd, symbol)

    # \begin{...} ... \end{...} → giữ nội dung bên trong
    t = re.sub(r'\\begin\{[^}]*\}', '', t)
    t = re.sub(r'\\end\{[^}]*\}', '', t)

    # Bỏ \\ (xuống dòng trong LaTeX) → space
    t = t.replace('\\\\', ' ')

    # Bỏ command LaTeX còn sót: \xxx (không theo sau bởi chữ)
    t = re.sub(r'\\[a-zA-Z]+\s*', ' ', t)

    # Bỏ {{ }} thừa → chỉ giữ nội dung
    for _ in range(3):
        t = re.sub(r'\{([^{}]*)\}', r'\1', t)

    # Dọn dẹp khoảng trắng thừa
    t = re.sub(r'  +', ' ', t)
    t = t.strip()

    return t


# Keyword gợi ý link chứa đề thi
_QUIZ_LINK_KEYWORDS = [
    "de-thi", "đề-thi", "de_thi", "bai-tap", "bài-tập", "bai_tap",
    "trac-nghiem", "trắc-nghiệm", "trac_nghiem", "cau-hoi", "câu-hỏi",
    "quiz", "exam", "test", "question", "exercise",
    "kiem-tra", "kiểm-tra", "on-tap", "ôn-tập", "luyen-tap", "luyện-tập",
]


class ExamCrawler:
    """Crawl và trích xuất câu hỏi từ trang web giáo dục.

    Hỗ trợ crawl sâu: nếu trang chính không có câu hỏi,
    sẽ tìm và đi theo các link con có khả năng chứa đề thi.
    """

    MAX_DEPTH = 2       # Tối đa đi sâu 2 cấp
    MAX_SUBPAGES = 5    # Tối đa crawl 5 trang con

    def __init__(self):
        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": CRAWLER_USER_AGENT,
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "vi,en;q=0.9",
        })
        self._visited: Set[str] = set()

    def crawl_url(self, url: str) -> dict:
        """Crawl URL và trích xuất câu hỏi.

        Nếu trang chính không có câu hỏi, tự động tìm link con
        có khả năng chứa đề thi và crawl tiếp (BFS, tối đa 2 cấp).

        Returns:
            dict: questions, title, raw_text, error, diagnosis, crawled_urls
        """
        self._visited.clear()
        result = self._empty_result()

        try:
            parsed = urlparse(url)
            if not parsed.scheme:
                url = "https://" + url

            # Crawl trang chính
            page = self._fetch_page(url)
            if page["error"]:
                result["error"] = page["error"]
                result["diagnosis"] = page["diagnosis"]
                return result

            result["title"] = page["title"]
            result["raw_text"] = page["raw_text"]
            result["crawled_urls"] = [url]

            if page["questions"]:
                result["questions"] = page["questions"][:CRAWLER_MAX_QUESTIONS_PER_PAGE]
                return result

            # Trang chính không có câu hỏi → tìm link con
            quiz_links = self._find_quiz_links(page["soup"], url)

            # Tìm tất cả link tiềm năng trên trang (kể cả chưa crawl)
            all_potential_links = self._find_quiz_links(page["soup"], url)
            # Cũng lấy thêm link sâu hơn — link đến bài cụ thể
            deeper_links = self._find_deep_quiz_links(page["soup"], url)

            if not quiz_links and not deeper_links:
                result["diagnosis"] = self._smart_diagnose(
                    page["raw_text"], url, page["soup"], [], []
                )
                return result

            # Crawl các link con (BFS)
            all_questions = []
            crawl_targets = (quiz_links + deeper_links)
            # Loại trùng, giữ thứ tự
            seen = set()
            unique_targets = []
            for u in crawl_targets:
                if u not in seen:
                    seen.add(u)
                    unique_targets.append(u)

            for sub_url in unique_targets[:self.MAX_SUBPAGES]:
                sub_page = self._fetch_page(sub_url)
                result["crawled_urls"].append(sub_url)
                if sub_page["questions"]:
                    all_questions.extend(sub_page["questions"])
                    if not result["title"] or result["title"] == "Đề thi từ web":
                        result["title"] = sub_page["title"]

            if all_questions:
                result["questions"] = all_questions[:CRAWLER_MAX_QUESTIONS_PER_PAGE]
                result["diagnosis"] = []
            else:
                # Tìm thêm link chưa crawl để gợi ý
                uncrawled = [u for u in unique_targets if u not in self._visited]
                extra_links = self._find_all_links_with_text(page["soup"], url)
                result["suggested_links"] = (uncrawled + extra_links)[:10]
                result["diagnosis"] = self._smart_diagnose(
                    page["raw_text"], url, page["soup"],
                    result["crawled_urls"], result["suggested_links"]
                )

            return result

        except Exception as e:
            result["error"] = f"Lỗi: {str(e)}"
            return result

    # ── Fetch & parse 1 trang ─────────────────────────────

    def _fetch_page(self, url: str) -> dict:
        """Fetch 1 trang, trả về questions + soup + metadata."""
        page = {"questions": [], "title": "", "raw_text": "", "soup": None,
                "error": None, "diagnosis": []}

        if url in self._visited:
            return page
        self._visited.add(url)

        try:
            resp = self._session.get(url, timeout=CRAWLER_REQUEST_TIMEOUT)
            resp.raise_for_status()
            # Ưu tiên encoding từ header, rồi meta tag, rồi apparent_encoding
            if resp.encoding and resp.encoding.lower() != "iso-8859-1":
                pass  # Giữ encoding từ header
            else:
                # Thử tìm encoding trong meta tag
                meta_match = re.search(
                    rb'<meta[^>]+charset=["\']?([a-zA-Z0-9-]+)', resp.content
                )
                if meta_match:
                    resp.encoding = meta_match.group(1).decode("ascii")
                else:
                    resp.encoding = resp.apparent_encoding or "utf-8"

            ct = resp.headers.get("Content-Type", "")
            if "text/html" not in ct and "application/xhtml" not in ct:
                page["error"] = f"Không phải HTML ({ct})"
                page["diagnosis"].append("Chỉ hỗ trợ trang HTML. File PDF/DOCX dùng chức năng Upload.")
                return page

            soup = BeautifulSoup(resp.text, "html.parser")
            page["title"] = self._extract_title(soup)

            # Giữ soup gốc cho việc tìm link (trước khi decompose)
            soup_for_links = BeautifulSoup(resp.text, "html.parser")
            page["soup"] = soup_for_links

            # Xóa thành phần không liên quan
            for tag in soup.find_all(["script", "style", "nav", "footer", "header",
                                      "aside", "iframe", "noscript", "form"]):
                tag.decompose()
            for sel in [".ads", ".ad", ".advertisement", ".sidebar", ".menu",
                        ".navigation", ".breadcrumb", ".comment", ".social",
                        ".share", ".related", "[class*='ad-']", "[class*='banner']"]:
                for el in soup.select(sel):
                    el.decompose()

            body_text = soup.get_text(strip=True)
            if len(body_text) < 200:
                page["diagnosis"].append(
                    "Trang có rất ít nội dung text — có thể dùng JavaScript để tải nội dung."
                )
                return page

            raw_text = self._extract_quiz_content(soup)
            page["raw_text"] = raw_text[:5000]

            if raw_text.strip():
                questions = self._parse_questions(raw_text)
                page["questions"] = questions

            return page

        except requests.exceptions.Timeout:
            page["error"] = f"Timeout (>{CRAWLER_REQUEST_TIMEOUT}s)"
            return page
        except requests.exceptions.ConnectionError:
            page["error"] = "Không thể kết nối"
            page["diagnosis"].append("Kiểm tra URL hoặc kết nối mạng.")
            return page
        except requests.exceptions.HTTPError as e:
            code = e.response.status_code
            page["error"] = f"HTTP {code}"
            if code == 403:
                page["diagnosis"].append("Trang chặn bot. Thử copy nội dung thủ công.")
            elif code == 404:
                page["diagnosis"].append("Trang không tồn tại.")
            return page
        except Exception as e:
            page["error"] = str(e)
            return page

    # ── Tìm link con chứa đề thi ─────────────────────────

    def _find_quiz_links(self, soup: Optional[BeautifulSoup], base_url: str) -> List[str]:
        """Tìm các link trên trang có khả năng dẫn đến đề thi."""
        if not soup:
            return []

        base_parsed = urlparse(base_url)
        base_domain = base_parsed.netloc
        links_scored: List[tuple] = []

        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            full_url = urljoin(base_url, href)
            parsed = urlparse(full_url)

            # Chỉ follow link cùng domain
            if parsed.netloc != base_domain:
                continue
            # Bỏ qua anchor, javascript, file downloads
            if href.startswith("#") or href.startswith("javascript:"):
                continue
            if any(href.endswith(ext) for ext in [".pdf", ".doc", ".docx", ".zip", ".rar"]):
                continue
            # Bỏ qua link đã visit
            if full_url in self._visited:
                continue

            # Tính score dựa trên URL và text
            score = self._score_link(full_url, a_tag.get_text(strip=True))
            if score > 0:
                links_scored.append((score, full_url))

        # Sắp xếp theo score giảm dần, lấy top
        links_scored.sort(key=lambda x: x[0], reverse=True)
        return [url for _, url in links_scored[:self.MAX_SUBPAGES]]

    def _score_link(self, url: str, link_text: str) -> int:
        """Tính điểm khả năng link chứa đề thi. 0 = không liên quan."""
        score = 0
        url_lower = url.lower()
        text_lower = link_text.lower()

        for kw in _QUIZ_LINK_KEYWORDS:
            if kw in url_lower:
                score += 3
            if kw in text_lower:
                score += 2

        # Bonus nếu text chứa từ khóa đề thi tiếng Việt
        vi_keywords = ["đề thi", "de thi", "trắc nghiệm", "trac nghiem",
                       "bài tập", "bai tap", "câu hỏi", "cau hoi",
                       "kiểm tra", "kiem tra", "ôn tập", "on tap",
                       "luyện tập", "luyen tap", "lớp", "lop", "môn", "mon"]
        for kw in vi_keywords:
            if kw in text_lower:
                score += 2

        return score

    # ── Trích xuất title ──────────────────────────────────

    def _extract_title(self, soup: BeautifulSoup) -> str:
        h1 = soup.find("h1")
        if h1 and h1.get_text(strip=True):
            return h1.get_text(strip=True)
        title_tag = soup.find("title")
        if title_tag and title_tag.get_text(strip=True):
            return title_tag.get_text(strip=True)
        return "Đề thi từ web"

    # ── Trích xuất nội dung đề thi ────────────────────────

    def _extract_quiz_content(self, soup: BeautifulSoup) -> str:
        """Trích xuất nội dung đề thi — ưu tiên vùng có câu hỏi đánh số."""

        # Chiến lược 1: Tìm vùng chứa nhiều pattern "Câu X" nhất
        best_area = self._find_quiz_area(soup)
        if best_area:
            text = self._area_to_text(best_area)
            if self._has_question_pattern(text):
                return text

        # Chiến lược 2: Tìm trong content area phổ biến
        for selector in ["article", ".post-content", ".entry-content", ".content",
                         ".article-body", "#content", "main", ".main-content",
                         ".quiz-content", ".exam-content", ".question-list"]:
            area = soup.select_one(selector)
            if area:
                text = self._area_to_text(area)
                if self._has_question_pattern(text):
                    return text

        # Chiến lược 3: Body
        body = soup.find("body")
        if body:
            return self._area_to_text(body)
        return ""

    def _find_quiz_area(self, soup: BeautifulSoup) -> Optional[Tag]:
        """Tìm thẻ HTML chứa nhiều câu hỏi đánh số nhất."""
        quiz_re = re.compile(r'(?:Câu|Question|Cau)\s*\d+\s*[.:)]', re.IGNORECASE)
        best_tag = None
        best_count = 0
        for tag in soup.find_all(["div", "article", "section", "main", "ol", "ul", "table"]):
            count = len(quiz_re.findall(tag.get_text()))
            if count > best_count:
                best_count = count
                best_tag = tag
        return best_tag if best_count >= 2 else None

    def _area_to_text(self, area: Tag) -> str:
        lines = []
        for el in area.find_all(["p", "li", "h1", "h2", "h3", "h4", "div", "span", "td", "th"]):
            if el.find_parent(["li", "td"]) and el.name in ["span", "div"]:
                continue
            text = el.get_text(strip=True)
            if text and len(text) > 1:
                lines.append(text)
        return "\n".join(lines)

    def _has_question_pattern(self, text: str) -> bool:
        for p in [r'(?:Câu|Question|Cau)\s*\d+\s*[.:)]', r'(?:^|\n)\s*\d+\s*[.)]\s*.{10,}']:
            if len(re.findall(p, text, re.IGNORECASE)) >= 2:
                return True
        return False

    # ── Parse câu hỏi ────────────────────────────────────

    _OPT_RE = re.compile(r'^\s*([A-Ea-e])\s*[.):\-]\s*(.+)', re.MULTILINE)
    _ANS_PATTERNS = [
        re.compile(r'(?:Đáp án|Dap an|Answer|Correct)\s*(?:đúng)?\s*[.:]\s*([A-Ea-e])', re.IGNORECASE),
        re.compile(r'([A-Ea-e])\s*[✓✔]'),
        re.compile(r'([A-Ea-e])\s*\(\s*(?:đúng|correct|right)\s*\)', re.IGNORECASE),
    ]

    # Các cụm spam cần loại bỏ khỏi nội dung câu hỏi
    _SPAM_PHRASES = [
        r'Bạn cần đăng ký.*?(?:VIP|gói|không giới hạn)[^.]*\.?',
        r'Nâng cấp VIP',
        r'Đăng ký.*?(?:tài khoản|thành viên|VIP)[^.]*\.?',
        r'Xem đáp án',
        r'Xem lời giải',
        r'Mua gói.*?(?:VIP|Premium)[^.]*\.?',
        r'Đăng nhập để xem[^.]*\.?',
        r'Click vào đây[^.]*\.?',
        r'Hãy đăng ký[^.]*\.?',
    ]

    def _preprocess_text(self, text: str) -> str:
        """Tiền xử lý text trước khi parse:
        - Tách options inline (A.xxxB.xxxC.xxx) thành từng dòng
        - Cắt bỏ phần lời giải, giữ đáp án
        - Loại bỏ spam VIP/đăng ký
        """
        # 1. Tách đáp án trước khi cắt lời giải: "Đáp án đúng: C" hoặc "Đáp án: B"
        #    (giữ lại thông tin này để parser tìm answer)

        # 2. Cắt bỏ lời giải — giữ "Đáp án đúng: X" nhưng bỏ phần giải thích sau
        #    Pattern: "Lời giải:Đáp án đúng: C<phần giải thích dài>"
        #    → giữ "Đáp án: C", bỏ phần còn lại
        text = re.sub(
            r'Lời giải\s*:?\s*(Đáp án\s*(?:đúng)?\s*:\s*[A-Ea-e]).*?(?=(?:Câu\s*\d+|$))',
            r'\n\1\n',
            text,
            flags=re.DOTALL | re.IGNORECASE,
        )
        # Trường hợp "Lời giải:" không có đáp án đúng → xóa luôn
        text = re.sub(
            r'Lời giải\s*:.*?(?=(?:Câu\s*\d+|$))',
            '\n',
            text,
            flags=re.DOTALL | re.IGNORECASE,
        )

        # 3. Loại bỏ spam VIP/đăng ký
        for spam_re in self._SPAM_PHRASES:
            text = re.sub(spam_re, '', text, flags=re.IGNORECASE)

        # 4. Tách inline options: "nội dungA.xxx B.yyy C.zzz D.www"
        #    Chèn newline trước mỗi option letter khi nó dính vào text trước
        #    Pattern: ký tự không phải whitespace/newline + A. → thêm \n trước A.
        text = re.sub(
            r'(?<=[^\s\n])([A-D])\s*[.)]\s*',
            r'\n\1. ',
            text,
        )

        # 5. Chèn newline trước "Đáp án:" nếu dính
        text = re.sub(
            r'(?<=[^\n])(Đáp án\s*(?:đúng)?\s*:)',
            r'\n\1',
            text,
            flags=re.IGNORECASE,
        )

        return text

    def _parse_questions(self, text: str) -> List[Question]:
        text = self._preprocess_text(text)
        questions = self._parse_numbered_questions(text)
        if not questions:
            questions = self._parse_by_options(text)
        return [q for q in questions if self._is_valid_question(q)]

    def _is_valid_question(self, q: Question) -> bool:
        c = q.content.strip()
        if len(c) < 15:
            return False

        # Loại bỏ câu có chứa spam dù dài
        c_lower = c.lower()
        hard_spam = ["đăng ký gói vip", "nâng cấp vip", "đăng nhập để xem",
                     "mua gói", "click vào đây", "hãy đăng ký"]
        if any(s in c_lower for s in hard_spam):
            return False

        looks_like_question = (
            c.endswith("?") or c.endswith(":") or c.endswith(".")
            or q.options
            or any(kw in c for kw in ["là gì", "bao nhiêu", "nào", "what", "which", "how"])
        )
        digit_count = sum(1 for ch in c if ch.isdigit())
        if digit_count > len(c) * 0.4 and not q.options:
            return False
        spam_words = ["đăng nhập", "đăng ký", "tải xuống", "download", "login",
                      "sign up", "subscribe", "cookie", "click",
                      "lượt xem"]
        if sum(1 for w in spam_words if w in c_lower) >= 1 and len(c) < 50 and not q.options:
            return False
        if not q.options and not looks_like_question:
            return False
        return True

    def _parse_numbered_questions(self, text: str) -> List[Question]:
        questions = []
        parts = re.split(r'(?:Câu|Question|Cau)\s*\d+\s*[.:)]', text, flags=re.IGNORECASE)
        headers = re.findall(r'(?:Câu|Question|Cau)\s*(\d+)\s*[.:)]', text, flags=re.IGNORECASE)

        if len(headers) < 2:
            numbered_pattern = r'\n\s*(\d+)\s*[.)]\s*'
            splits = re.split(numbered_pattern, text)
            if len(splits) >= 5:
                headers = []
                parts = []
                for i in range(1, len(splits) - 1, 2):
                    content = splits[i + 1] if i + 1 < len(splits) else ""
                    if content.strip() and len(content.strip()) > 10:
                        headers.append(splits[i])
                        parts.append(content)
        else:
            if parts and len(parts) > len(headers):
                parts = parts[1:]

        for num, part in zip(headers, parts):
            q = self._parse_single_question(part.strip())
            if q:
                questions.append(q)
        return questions

    def _parse_by_options(self, text: str) -> List[Question]:
        questions = []
        option_positions = [(m.start(), m) for m in self._OPT_RE.finditer(text)]
        if len(option_positions) < 4:
            return []

        groups = []
        current_group = [option_positions[0]]
        for i in range(1, len(option_positions)):
            pos = option_positions[i][0]
            prev_pos = option_positions[i-1][0]
            if pos - prev_pos < 500:
                current_group.append(option_positions[i])
            else:
                if len(current_group) >= 3:
                    groups.append(current_group)
                current_group = [option_positions[i]]
        if len(current_group) >= 3:
            groups.append(current_group)

        for group in groups:
            first_pos = group[0][0]
            before = text[max(0, first_pos - 500):first_pos]
            lines = [l.strip() for l in before.split('\n') if l.strip()]
            content = lines[-1] if lines else ""
            if not content or len(content) < 5:
                continue

            options = [f"{m.group(1).upper()}. {m.group(2).strip()}" for _, m in group]
            last_end = group[-1][1].end()
            after = text[last_end:last_end + 200]
            answer = ""
            for pat in self._ANS_PATTERNS:
                m = pat.search(after)
                if m:
                    answer = m.group(1).upper()
                    break

            questions.append(Question(
                id=str(uuid.uuid4()), content=_latex_to_text(content),
                options=[_latex_to_text(o) for o in options],
                answer=answer, question_type="trac_nghiem",
            ))
        return questions

    def _parse_single_question(self, text: str) -> Optional[Question]:
        if not text:
            return None
        lines = text.split('\n')
        content_lines, options, answer = [], [], ""
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            # Bỏ qua dòng spam
            stripped_lower = stripped.lower()
            if any(s in stripped_lower for s in [
                "đăng ký", "nâng cấp vip", "xem đáp án", "xem lời giải",
                "đăng nhập để", "click vào", "mua gói",
            ]):
                continue
            # Bỏ qua dòng "Lời giải:" còn sót
            if re.match(r'^Lời giải\s*:', stripped, re.IGNORECASE):
                continue

            opt_match = self._OPT_RE.match(stripped)
            if opt_match:
                options.append(f"{opt_match.group(1).upper()}. {opt_match.group(2).strip()}")
            else:
                ans_found = False
                for pat in self._ANS_PATTERNS:
                    m = pat.search(stripped)
                    if m:
                        answer = m.group(1).upper()
                        ans_found = True
                        break
                if not ans_found:
                    content_lines.append(stripped)

        content = ' '.join(content_lines).strip()
        # Loại bỏ "Đáp án đúng: X" còn sót trong content
        content = re.sub(
            r'\s*Đáp án\s*(?:đúng)?\s*:\s*[A-Ea-e]\s*$', '', content, flags=re.IGNORECASE
        ).strip()
        if not content or len(content) < 5:
            return None
        # Chuyển LaTeX → text đọc được
        content = _latex_to_text(content)
        options = [_latex_to_text(opt) for opt in options]
        return Question(
            id=str(uuid.uuid4()), content=content,
            options=options, answer=answer,
            question_type="trac_nghiem" if options else "tu_luan",
        )

    # ── Chẩn đoán & utils ────────────────────────────────

    def _diagnose_failure(self, raw_text: str) -> List[str]:
        diagnosis = []
        if len(raw_text) < 100:
            diagnosis.append("Nội dung trích xuất quá ngắn. Trang có thể dùng JavaScript để tải nội dung.")
        else:
            has_cau = bool(re.search(r'(?:Câu|Question|Cau)\s*\d+', raw_text, re.IGNORECASE))
            has_options = bool(re.search(r'[A-D]\s*[.):]', raw_text))
            if not has_cau:
                diagnosis.append(
                    "Không tìm thấy câu hỏi đánh số (Câu 1, Câu 2, ... hoặc 1., 2., ...). "
                    "Trang có thể không chứa đề thi dạng chuẩn."
                )
            elif not has_options:
                diagnosis.append("Tìm thấy câu đánh số nhưng không có đáp án A/B/C/D.")
            else:
                diagnosis.append("Tìm thấy pattern câu hỏi nhưng cấu trúc HTML không tương thích.")

        diagnosis.append("Gợi ý: Copy nội dung đề thi → dán vào Upload (tab Nhập trực tiếp).")
        return diagnosis

    def _find_deep_quiz_links(self, soup: Optional[BeautifulSoup], base_url: str) -> List[str]:
        """Tìm link đến bài cụ thể — link có số (bài 1, đề 3, câu hỏi, page/2...)."""
        if not soup:
            return []

        base_parsed = urlparse(base_url)
        base_domain = base_parsed.netloc
        results: List[tuple] = []

        # Pattern: link có số trong URL hoặc text (thường là bài cụ thể, không phải danh mục)
        num_url_re = re.compile(r'(?:bai|de|cau|page|p|question|q|quiz|test)[-_/]?\d+', re.IGNORECASE)
        num_text_re = re.compile(
            r'(?:bài|đề|câu|đề thi|đề số|bài tập|phần)\s*\d+', re.IGNORECASE
        )

        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            full_url = urljoin(base_url, href)
            parsed = urlparse(full_url)

            if parsed.netloc != base_domain:
                continue
            if href.startswith("#") or href.startswith("javascript:"):
                continue
            if full_url in self._visited:
                continue

            text = a_tag.get_text(strip=True)
            score = 0

            # URL chứa pattern bài cụ thể
            if num_url_re.search(full_url):
                score += 4
            # Text chứa pattern bài cụ thể
            if num_text_re.search(text):
                score += 5
            # Text ngắn + có số → thường là link đến 1 bài cụ thể
            if text and len(text) < 60 and re.search(r'\d+', text):
                score += 1
            # URL dài hơn base → sâu hơn → có thể là bài cụ thể
            if len(parsed.path) > len(urlparse(base_url).path) + 5:
                score += 1

            if score >= 3:
                results.append((score, full_url))

        results.sort(key=lambda x: x[0], reverse=True)
        return [url for _, url in results[:self.MAX_SUBPAGES]]

    def _find_all_links_with_text(self, soup: Optional[BeautifulSoup], base_url: str) -> List[str]:
        """Lấy tất cả link trên trang có text liên quan đến đề thi/quiz, chưa crawl."""
        if not soup:
            return []

        base_domain = urlparse(base_url).netloc
        results: List[tuple] = []

        quiz_text_re = re.compile(
            r'(?:đề|de|bài|bai|câu|cau|trắc nghiệm|trac nghiem|kiểm tra|kiem tra|'
            r'quiz|exam|test|question|ôn tập|on tap|luyện|luyen|lớp|lop|môn|mon|'
            r'toán|toan|lý|ly|hóa|hoa|văn|van|sử|su|địa|dia|anh|sinh|gdcd|tin)',
            re.IGNORECASE
        )

        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            full_url = urljoin(base_url, href)
            parsed = urlparse(full_url)

            if parsed.netloc != base_domain:
                continue
            if href.startswith("#") or href.startswith("javascript:"):
                continue
            if full_url in self._visited or full_url == base_url:
                continue

            text = a_tag.get_text(strip=True)
            if not text or len(text) < 3:
                continue

            # Ưu tiên link có text liên quan đề thi
            score = 0
            if quiz_text_re.search(text):
                score += 3
            if quiz_text_re.search(full_url):
                score += 2
            if score > 0:
                results.append((score, full_url))

        results.sort(key=lambda x: x[0], reverse=True)
        return [url for _, url in results[:15]]

    def _smart_diagnose(
        self, raw_text: str, url: str, soup: Optional[BeautifulSoup],
        crawled_urls: List[str], suggested_links: List[str]
    ) -> List[str]:
        """Chẩn đoán thông minh — phân tích tình huống cụ thể, không trả lời máy móc."""
        diagnosis = []
        parsed = urlparse(url)
        domain = parsed.netloc
        path = parsed.path.rstrip("/")

        # ── 1. Phân tích nội dung trang ──
        text_len = len(raw_text) if raw_text else 0

        if text_len < 100:
            diagnosis.append(
                f"Trang **{domain}** trả về rất ít nội dung ({text_len} ký tự). "
                f"Rất có thể trang dùng JavaScript (React/Vue/Angular) để tải đề thi — "
                f"crawler chỉ đọc được HTML tĩnh."
            )
        else:
            # Phân tích chi tiết có gì trong text
            has_numbered = bool(re.search(r'(?:Câu|Question|Cau)\s*\d+', raw_text, re.IGNORECASE))
            has_options = bool(re.search(r'\n\s*[A-D]\s*[.):]', raw_text))
            has_digits_numbered = bool(re.search(r'\n\s*\d+[.)]\s*.{10,}', raw_text))

            if has_numbered and has_options:
                diagnosis.append(
                    "Trang có cả câu hỏi đánh số lẫn đáp án A/B/C/D nhưng cấu trúc HTML "
                    "không theo định dạng chuẩn mà crawler hỗ trợ. "
                    "Cách nhanh nhất: **copy toàn bộ phần đề thi** từ trang → dán vào **Upload > Nhập trực tiếp**."
                )
            elif has_numbered and not has_options:
                diagnosis.append(
                    "Trang có câu hỏi đánh số nhưng **không tìm thấy đáp án A/B/C/D**. "
                    "Có thể đây là dạng tự luận hoặc đáp án nằm ở trang khác."
                )
            elif has_digits_numbered:
                diagnosis.append(
                    "Trang có nội dung đánh số (1, 2, 3...) nhưng không rõ ràng là câu hỏi. "
                    "Có thể đây là trang mục lục hoặc danh sách bài viết, không phải đề thi trực tiếp."
                )
            else:
                diagnosis.append(
                    f"Nội dung trang ({text_len} ký tự) không chứa câu hỏi đánh số rõ ràng. "
                    f"Đây có thể là trang danh mục, trang chủ, hoặc trang giới thiệu — "
                    f"cần vào link bài cụ thể bên trong."
                )

        # ── 2. Phân tích URL — trang chủ hay trang sâu? ──
        path_depth = len([p for p in path.split("/") if p])
        if path_depth <= 1:
            diagnosis.append(
                f"URL hiện tại ({domain}{path}) là **trang cấp cao** (trang chủ/danh mục). "
                f"Đề thi thường nằm ở các trang con bên trong — thử vào link cụ thể hơn."
            )

        # ── 3. Phân tích kết quả crawl sâu ──
        num_crawled = len(crawled_urls) if crawled_urls else 0
        if num_crawled > 1:
            diagnosis.append(
                f"Đã thử crawl **{num_crawled} trang** (cả trang chính và trang con) "
                f"nhưng không trang nào chứa câu hỏi ở dạng có thể trích xuất được."
            )

        # ── 4. Gợi ý dựa trên link tìm được ──
        if suggested_links:
            n = len(suggested_links)
            diagnosis.append(
                f"Tìm thấy **{n} link** có thể chứa đề thi trên trang. "
                f"Bạn có thể thử crawl trực tiếp từng link bên dưới."
            )
        else:
            diagnosis.append(
                "Không tìm thấy link nào trên trang có vẻ dẫn đến đề thi cụ thể."
            )

        # ── 5. Gợi ý hành động cụ thể (không máy móc) ──
        if soup:
            # Đếm tổng link trên trang
            all_links = soup.find_all("a", href=True)
            n_links = len(all_links)
            if n_links > 20:
                diagnosis.append(
                    f"Trang có **{n_links} link** — rất có thể là trang danh sách. "
                    f"Mở trang trong trình duyệt → tìm đúng bài đề thi → copy URL đó."
                )

        # Gợi ý cuối cùng — luôn hữu ích
        diagnosis.append(
            "**Mẹo**: Nếu crawler không hoạt động, mở trang trong trình duyệt → "
            "bôi đen toàn bộ đề thi → Ctrl+C → vào **Upload > tab Nhập trực tiếp** → Ctrl+V."
        )

        return diagnosis

    def _short_url(self, url: str) -> str:
        parsed = urlparse(url)
        path = parsed.path.rstrip("/")
        if len(path) > 40:
            path = path[:20] + "..." + path[-15:]
        return parsed.netloc + path

    @staticmethod
    def _empty_result() -> dict:
        return {"questions": [], "title": "", "raw_text": "", "error": None,
                "diagnosis": [], "crawled_urls": [], "suggested_links": []}
