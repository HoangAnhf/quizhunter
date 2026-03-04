"""Ngân hàng câu hỏi — load từ JSON files trong data/question_bank/.

Lazy-loading: mỗi file JSON chỉ đọc 1 lần, cache trong bộ nhớ.
"""
import json
import functools
from typing import List, Optional, Dict
from pathlib import Path

from backend.schemas.exam import Question
from config import QUESTION_BANK_DIR, VI_SUBJECT_FILES


@functools.lru_cache(maxsize=16)
def _load_subject_file(subject: str) -> tuple:
    """Đọc và cache file JSON của 1 môn. Trả về tuple of dicts (hashable cho LRU)."""
    filename = VI_SUBJECT_FILES.get(subject)
    if not filename:
        return ()
    filepath = QUESTION_BANK_DIR / filename
    if not filepath.exists():
        return ()
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    return tuple(data.get("questions", []))


def get_questions(
    subject: str,
    grade: Optional[int] = None,
    difficulty: Optional[str] = None,
    question_type: Optional[str] = None,
    topic: Optional[str] = None,
    limit: Optional[int] = None,
) -> List[Question]:
    """Lấy câu hỏi từ ngân hàng với bộ lọc tùy chọn."""
    raw_questions = _load_subject_file(subject)
    results = []
    for q_data in raw_questions:
        if grade is not None and q_data.get("grade") != grade:
            continue
        if difficulty and q_data.get("difficulty") != difficulty:
            continue
        if question_type and q_data.get("question_type") != question_type:
            continue
        if topic and topic.lower() not in (q_data.get("topic") or "").lower():
            continue
        results.append(Question.from_dict(q_data))
        if limit and len(results) >= limit:
            break
    return results


def get_questions_grouped(
    subject: str,
    grade: Optional[int] = None,
    difficulty: Optional[str] = None,
) -> Dict[str, List[Question]]:
    """Lấy câu hỏi nhóm theo loại — tương thích với _search_vietnamese()."""
    questions = get_questions(subject, grade=grade, difficulty=difficulty)
    if not questions:
        return {}

    groups: Dict[str, List[Question]] = {}
    for q in questions:
        if q.question_type == "trac_nghiem":
            label = "Trắc nghiệm"
        elif q.question_type == "tu_luan":
            label = "Điền đáp án"
        elif q.question_type == "noi_cot":
            label = "Nối cột"
        else:
            label = "Bài tập"
        groups.setdefault(label, []).append(q)

    return {f"{label} ({len(qs)} câu)": qs for label, qs in groups.items()}


def get_bank_stats() -> Dict:
    """Thống kê toàn bộ ngân hàng câu hỏi."""
    stats = {"total": 0, "by_subject": {}, "by_grade": {}, "by_difficulty": {}}
    for subject in VI_SUBJECT_FILES:
        raw = _load_subject_file(subject)
        count = len(raw)
        stats["total"] += count
        stats["by_subject"][subject] = count
        for q in raw:
            g = q.get("grade", 0)
            d = q.get("difficulty", "trung_binh")
            stats["by_grade"][g] = stats["by_grade"].get(g, 0) + 1
            stats["by_difficulty"][d] = stats["by_difficulty"].get(d, 0) + 1
    return stats


def clear_cache():
    """Xóa cache — gọi sau khi cập nhật file JSON."""
    _load_subject_file.cache_clear()
