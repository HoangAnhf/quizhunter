import json
from typing import List, Optional
from datetime import datetime, timezone

import mysql.connector
from mysql.connector import pooling

from backend.schemas.exam import Exam, Question
from config import MYSQL_CONFIG, VI_SUBJECT_CODES, DIFFICULTY_CODES

# Connection pool — tái sử dụng connection, tránh mở/đóng liên tục
_pool = pooling.MySQLConnectionPool(
    pool_name="quizhunter_pool",
    pool_size=5,
    **MYSQL_CONFIG,
)


def _get_conn():
    return _pool.get_connection()


def _row_to_question(row: dict) -> Question:
    """Convert MySQL row → Question object."""
    return Question(
        id=row["id"],
        content=row["content"],
        options=json.loads(row["options"]) if row["options"] else [],
        answer=row["answer"] or "",
        question_type=row["question_type"],
        grade=row["grade"],
        topic=row.get("topic"),
        solution=row.get("solution"),
        comment=row.get("comment"),
        column_a=json.loads(row["column_a"]) if row.get("column_a") else None,
        column_b=json.loads(row["column_b"]) if row.get("column_b") else None,
    )


class MySQLExamStore:
    """Quản lý CRUD kho đề thi, lưu trong MySQL."""

    # ── Question CRUD ─────────────────────────────────────────

    def save_question(self, q: Question, subject: str, difficulty: str = "trung_binh") -> str:
        conn = _get_conn()
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO questions (id, content, options, answer, question_type,
                    subject, grade, difficulty, topic, solution, comment, column_a, column_b)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    content=VALUES(content), options=VALUES(options),
                    answer=VALUES(answer), question_type=VALUES(question_type),
                    subject=VALUES(subject), grade=VALUES(grade),
                    difficulty=VALUES(difficulty), topic=VALUES(topic),
                    solution=VALUES(solution), comment=VALUES(comment),
                    column_a=VALUES(column_a), column_b=VALUES(column_b)
            """, (
                q.id, q.content,
                json.dumps(q.options, ensure_ascii=False),
                q.answer, q.question_type, subject, q.grade, difficulty,
                q.topic, q.solution, q.comment,
                json.dumps(q.column_a, ensure_ascii=False) if q.column_a else None,
                json.dumps(q.column_b, ensure_ascii=False) if q.column_b else None,
            ))
            conn.commit()
            return q.id
        finally:
            cur.close()
            conn.close()

    def get_questions(
        self,
        subject: Optional[str] = None,
        grade: Optional[int] = None,
        difficulty: Optional[str] = None,
        question_type: Optional[str] = None,
        search_text: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Question]:
        conn = _get_conn()
        cur = conn.cursor(dictionary=True)
        try:
            where, params = [], []
            if subject:
                where.append("subject = %s")
                params.append(subject)
            if grade:
                where.append("grade = %s")
                params.append(grade)
            if difficulty:
                where.append("difficulty = %s")
                params.append(difficulty)
            if question_type:
                where.append("question_type = %s")
                params.append(question_type)
            if search_text:
                where.append("MATCH(content) AGAINST(%s IN NATURAL LANGUAGE MODE)")
                params.append(search_text)

            sql = "SELECT * FROM questions"
            if where:
                sql += " WHERE " + " AND ".join(where)
            sql += " ORDER BY id LIMIT %s OFFSET %s"
            params.extend([limit, offset])

            cur.execute(sql, params)
            return [_row_to_question(row) for row in cur.fetchall()]
        finally:
            cur.close()
            conn.close()

    def count_questions(
        self,
        subject: Optional[str] = None,
        grade: Optional[int] = None,
        difficulty: Optional[str] = None,
    ) -> int:
        conn = _get_conn()
        cur = conn.cursor()
        try:
            where, params = [], []
            if subject:
                where.append("subject = %s")
                params.append(subject)
            if grade:
                where.append("grade = %s")
                params.append(grade)
            if difficulty:
                where.append("difficulty = %s")
                params.append(difficulty)

            sql = "SELECT COUNT(*) FROM questions"
            if where:
                sql += " WHERE " + " AND ".join(where)

            cur.execute(sql, params)
            return cur.fetchone()[0]
        finally:
            cur.close()
            conn.close()

    def search_questions_fulltext(self, text: str, limit: int = 50) -> List[Question]:
        """Tìm kiếm fulltext tiếng Việt trong nội dung câu hỏi."""
        conn = _get_conn()
        cur = conn.cursor(dictionary=True)
        try:
            cur.execute("""
                SELECT *, MATCH(content) AGAINST(%s IN NATURAL LANGUAGE MODE) AS relevance
                FROM questions
                WHERE MATCH(content) AGAINST(%s IN NATURAL LANGUAGE MODE)
                ORDER BY relevance DESC
                LIMIT %s
            """, (text, text, limit))
            return [_row_to_question(row) for row in cur.fetchall()]
        finally:
            cur.close()
            conn.close()

    # ── Exam CRUD ─────────────────────────────────────────────

    def _generate_exam_code(self, subject: str, grade, difficulty: str) -> str:
        """Tạo mã đề ngắn: TOAN-8-CB-001."""
        subj_code = VI_SUBJECT_CODES.get(subject, subject[:4].upper())
        diff_code = DIFFICULTY_CODES.get(difficulty, "HH")
        prefix = f"{subj_code}-{grade}-{diff_code}" if grade else f"{subj_code}-{diff_code}"

        conn = _get_conn()
        cur = conn.cursor()
        try:
            cur.execute(
                "SELECT MAX(CAST(SUBSTRING_INDEX(exam_code, '-', -1) AS UNSIGNED)) FROM exams WHERE exam_code LIKE %s",
                (prefix + "-%",),
            )
            max_seq = cur.fetchone()[0] or 0
            return f"{prefix}-{max_seq + 1:03d}"
        finally:
            cur.close()
            conn.close()

    def save(self, exam: Exam) -> str:
        # Auto-generate exam_code nếu chưa có
        if not exam.exam_code:
            exam.exam_code = self._generate_exam_code(exam.subject, exam.grade, exam.difficulty)

        conn = _get_conn()
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO exams (id, title, subject, difficulty, source_file, grade, created_at, exam_code)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    title=VALUES(title), subject=VALUES(subject),
                    difficulty=VALUES(difficulty), source_file=VALUES(source_file),
                    grade=VALUES(grade), exam_code=VALUES(exam_code)
            """, (
                exam.id, exam.title, exam.subject, exam.difficulty,
                exam.source_file, exam.grade,
                datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                exam.exam_code,
            ))

            # Xóa liên kết cũ rồi insert lại
            cur.execute("DELETE FROM exam_questions WHERE exam_id = %s", (exam.id,))
            for i, q in enumerate(exam.questions):
                # Insert question trong cùng connection (tránh deadlock)
                cur.execute("""
                    INSERT INTO questions (id, content, options, answer, question_type,
                        subject, grade, difficulty, topic, solution, comment, column_a, column_b)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        content=VALUES(content), options=VALUES(options),
                        answer=VALUES(answer), question_type=VALUES(question_type),
                        subject=VALUES(subject), grade=VALUES(grade),
                        difficulty=VALUES(difficulty), topic=VALUES(topic),
                        solution=VALUES(solution), comment=VALUES(comment),
                        column_a=VALUES(column_a), column_b=VALUES(column_b)
                """, (
                    q.id, q.content,
                    json.dumps(q.options, ensure_ascii=False),
                    q.answer, q.question_type, exam.subject, q.grade, exam.difficulty,
                    q.topic, q.solution, q.comment,
                    json.dumps(q.column_a, ensure_ascii=False) if q.column_a else None,
                    json.dumps(q.column_b, ensure_ascii=False) if q.column_b else None,
                ))
                cur.execute(
                    "INSERT IGNORE INTO exam_questions (exam_id, question_id, position) VALUES (%s, %s, %s)",
                    (exam.id, q.id, i),
                )

            conn.commit()
            return exam.id
        finally:
            cur.close()
            conn.close()

    def get_all(
        self,
        subject: Optional[str] = None,
        difficulty: Optional[str] = None,
        grade: Optional[int] = None,
        page: int = 1,
        per_page: int = 10,
    ) -> List[Exam]:
        conn = _get_conn()
        cur = conn.cursor(dictionary=True)
        try:
            where, params = [], []
            if subject:
                where.append("subject = %s")
                params.append(subject)
            if difficulty:
                where.append("difficulty = %s")
                params.append(difficulty)
            if grade:
                where.append("grade = %s")
                params.append(grade)

            sql = "SELECT * FROM exams"
            if where:
                sql += " WHERE " + " AND ".join(where)
            sql += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
            params.extend([per_page, (page - 1) * per_page])

            cur.execute(sql, params)
            exams = []
            for row in cur.fetchall():
                exam = self._row_to_exam_with_questions(row, cur, conn)
                exams.append(exam)
            return exams
        finally:
            cur.close()
            conn.close()

    def get_by_id(self, exam_id: str) -> Optional[Exam]:
        conn = _get_conn()
        cur = conn.cursor(dictionary=True)
        try:
            cur.execute("SELECT * FROM exams WHERE id = %s", (exam_id,))
            row = cur.fetchone()
            if not row:
                return None
            return self._row_to_exam_with_questions(row, cur, conn)
        finally:
            cur.close()
            conn.close()

    def delete(self, exam_id: str) -> bool:
        conn = _get_conn()
        cur = conn.cursor()
        try:
            cur.execute("DELETE FROM exams WHERE id = %s", (exam_id,))
            conn.commit()
            return cur.rowcount > 0
        finally:
            cur.close()
            conn.close()

    def count(
        self,
        subject: Optional[str] = None,
        difficulty: Optional[str] = None,
        grade: Optional[int] = None,
    ) -> int:
        conn = _get_conn()
        cur = conn.cursor()
        try:
            where, params = [], []
            if subject:
                where.append("subject = %s")
                params.append(subject)
            if difficulty:
                where.append("difficulty = %s")
                params.append(difficulty)
            if grade:
                where.append("grade = %s")
                params.append(grade)

            sql = "SELECT COUNT(*) FROM exams"
            if where:
                sql += " WHERE " + " AND ".join(where)

            cur.execute(sql, params)
            return cur.fetchone()[0]
        finally:
            cur.close()
            conn.close()

    def get_stats(self) -> dict:
        conn = _get_conn()
        cur = conn.cursor(dictionary=True)
        try:
            cur.execute("SELECT COUNT(*) AS cnt FROM exams")
            total_exams = cur.fetchone()["cnt"]

            cur.execute("SELECT COUNT(*) AS cnt FROM questions")
            total_questions = cur.fetchone()["cnt"]

            cur.execute("SELECT subject, COUNT(*) AS cnt FROM exams GROUP BY subject")
            subjects = {row["subject"]: row["cnt"] for row in cur.fetchall()}

            cur.execute("SELECT difficulty, COUNT(*) AS cnt FROM exams GROUP BY difficulty")
            difficulties = {row["difficulty"]: row["cnt"] for row in cur.fetchall()}

            cur.execute("SELECT COUNT(*) AS cnt FROM search_history")
            total_searches = cur.fetchone()["cnt"]

            return {
                "total_exams": total_exams,
                "total_questions": total_questions,
                "subjects": subjects,
                "difficulties": difficulties,
                "total_searches": total_searches,
            }
        finally:
            cur.close()
            conn.close()

    def increment_search_count(self, query: str = "", results_count: int = 0):
        conn = _get_conn()
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO search_history (query, results_count) VALUES (%s, %s)",
                (query, results_count),
            )
            conn.commit()
        finally:
            cur.close()
            conn.close()

    def get_recent_searches(self, limit: int = 10) -> List[str]:
        """Lấy các từ khóa tìm kiếm gần đây (unique)."""
        conn = _get_conn()
        cur = conn.cursor()
        try:
            cur.execute(
                "SELECT query FROM search_history WHERE query != '' ORDER BY searched_at DESC LIMIT 50"
            )
            seen = set()
            result = []
            for (q,) in cur.fetchall():
                if q not in seen:
                    seen.add(q)
                    result.append(q)
                    if len(result) >= limit:
                        break
            return result
        finally:
            cur.close()
            conn.close()

    def get_all_exams_unfiltered(self) -> List[Exam]:
        """Lấy toàn bộ đề thi không phân trang."""
        conn = _get_conn()
        cur = conn.cursor(dictionary=True)
        try:
            cur.execute("SELECT * FROM exams ORDER BY created_at DESC")
            exams = []
            for row in cur.fetchall():
                exam = self._row_to_exam_with_questions(row, cur, conn)
                exams.append(exam)
            return exams
        finally:
            cur.close()
            conn.close()

    def search_by_code_or_title(
        self,
        query: str,
        subject: Optional[str] = None,
        difficulty: Optional[str] = None,
        grade: Optional[int] = None,
        page: int = 1,
        per_page: int = 10,
    ) -> tuple:
        """Tìm đề theo mã đề hoặc tên. Trả về (List[Exam], total_count)."""
        conn = _get_conn()
        cur = conn.cursor(dictionary=True)
        try:
            where = ["(exam_code LIKE %s OR title LIKE %s)"]
            like = f"%{query}%"
            params = [like, like]

            if subject:
                where.append("subject = %s")
                params.append(subject)
            if difficulty:
                where.append("difficulty = %s")
                params.append(difficulty)
            if grade:
                where.append("grade = %s")
                params.append(grade)

            where_sql = " AND ".join(where)

            cur.execute(f"SELECT COUNT(*) AS cnt FROM exams WHERE {where_sql}", params)
            total = cur.fetchone()["cnt"]

            cur.execute(
                f"SELECT * FROM exams WHERE {where_sql} ORDER BY exam_code LIMIT %s OFFSET %s",
                params + [per_page, (page - 1) * per_page],
            )
            exams = [self._row_to_exam_with_questions(row, cur, conn) for row in cur.fetchall()]
            return exams, total
        finally:
            cur.close()
            conn.close()

    def backfill_exam_codes(self) -> int:
        """Tạo mã đề cho các đề cũ chưa có exam_code. Trả về số đề đã cập nhật."""
        conn = _get_conn()
        cur = conn.cursor(dictionary=True)
        try:
            cur.execute("SELECT id, subject, grade, difficulty FROM exams WHERE exam_code IS NULL ORDER BY created_at")
            rows = cur.fetchall()
            if not rows:
                return 0

            # Track sequences locally để tránh conflict khi chưa commit
            prefix_seq: dict[str, int] = {}
            for row in rows:
                subj_code = VI_SUBJECT_CODES.get(row["subject"], row["subject"][:4].upper())
                diff_code = DIFFICULTY_CODES.get(row["difficulty"], "HH")
                grade = row.get("grade")
                prefix = f"{subj_code}-{grade}-{diff_code}" if grade else f"{subj_code}-{diff_code}"

                if prefix not in prefix_seq:
                    # Lấy MAX hiện tại từ DB cho prefix này
                    cur2 = conn.cursor()
                    cur2.execute(
                        "SELECT MAX(CAST(SUBSTRING_INDEX(exam_code, '-', -1) AS UNSIGNED)) FROM exams WHERE exam_code LIKE %s",
                        (prefix + "-%",),
                    )
                    prefix_seq[prefix] = cur2.fetchone()[0] or 0
                    cur2.close()

                prefix_seq[prefix] += 1
                code = f"{prefix}-{prefix_seq[prefix]:03d}"

                cur2 = conn.cursor()
                cur2.execute("UPDATE exams SET exam_code = %s WHERE id = %s", (code, row["id"]))
                cur2.close()

            conn.commit()
            return len(rows)
        finally:
            cur.close()
            conn.close()

    # ── Random exam generator ────────────────────────────────

    def generate_random_exam(
        self,
        subject: str,
        grade: Optional[int] = None,
        difficulty: Optional[str] = None,
        num_questions: int = 20,
    ) -> List[Question]:
        """Tạo đề ngẫu nhiên từ MySQL — tính năng mới!"""
        conn = _get_conn()
        cur = conn.cursor(dictionary=True)
        try:
            where, params = ["subject = %s"], [subject]
            if grade:
                where.append("grade = %s")
                params.append(grade)
            if difficulty:
                where.append("difficulty = %s")
                params.append(difficulty)

            sql = f"SELECT * FROM questions WHERE {' AND '.join(where)} ORDER BY RAND() LIMIT %s"
            params.append(num_questions)

            cur.execute(sql, params)
            return [_row_to_question(row) for row in cur.fetchall()]
        finally:
            cur.close()
            conn.close()

    # ── Quiz / Làm đề ──────────────────────────────────────────

    def create_quiz_session(self, session_id: str, exam_id: str, total: int) -> str:
        conn = _get_conn()
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO quiz_sessions (id, exam_id, total) VALUES (%s, %s, %s)",
                (session_id, exam_id, total),
            )
            conn.commit()
            return session_id
        finally:
            cur.close()
            conn.close()

    def complete_quiz_session(self, session_id: str, score: int, time_spent: int) -> None:
        conn = _get_conn()
        cur = conn.cursor()
        try:
            cur.execute(
                "UPDATE quiz_sessions SET completed_at = NOW(), score = %s, time_spent_seconds = %s WHERE id = %s",
                (score, time_spent, session_id),
            )
            conn.commit()
        finally:
            cur.close()
            conn.close()

    def save_quiz_answers(self, session_id: str, answers: list) -> None:
        """answers: list of dict {question_id, user_answer, is_correct}"""
        conn = _get_conn()
        cur = conn.cursor()
        try:
            for a in answers:
                cur.execute(
                    "INSERT INTO quiz_answers (session_id, question_id, user_answer, is_correct) VALUES (%s, %s, %s, %s)",
                    (session_id, a["question_id"], a["user_answer"], 1 if a["is_correct"] else 0),
                )
            conn.commit()
        finally:
            cur.close()
            conn.close()

    def get_quiz_history(self, limit: int = 50) -> list:
        """Lấy lịch sử làm đề gần đây."""
        conn = _get_conn()
        cur = conn.cursor(dictionary=True)
        try:
            cur.execute("""
                SELECT qs.*, e.title, e.subject, e.difficulty, e.exam_code, e.grade
                FROM quiz_sessions qs
                JOIN exams e ON qs.exam_id = e.id
                WHERE qs.completed_at IS NOT NULL
                ORDER BY qs.completed_at DESC
                LIMIT %s
            """, (limit,))
            return cur.fetchall()
        finally:
            cur.close()
            conn.close()

    def get_quiz_session_detail(self, session_id: str) -> dict:
        """Lấy chi tiết 1 lần làm đề + câu trả lời."""
        conn = _get_conn()
        cur = conn.cursor(dictionary=True)
        try:
            cur.execute("""
                SELECT qs.*, e.title, e.subject, e.difficulty, e.exam_code
                FROM quiz_sessions qs JOIN exams e ON qs.exam_id = e.id
                WHERE qs.id = %s
            """, (session_id,))
            session = cur.fetchone()
            if not session:
                return {}

            cur.execute("""
                SELECT qa.*, q.content, q.options, q.answer AS correct_answer,
                       q.question_type, q.column_a, q.column_b
                FROM quiz_answers qa JOIN questions q ON qa.question_id = q.id
                WHERE qa.session_id = %s ORDER BY qa.id
            """, (session_id,))
            answers = cur.fetchall()
            for a in answers:
                a["options"] = json.loads(a["options"]) if a["options"] else []
                a["column_a"] = json.loads(a["column_a"]) if a.get("column_a") else None
                a["column_b"] = json.loads(a["column_b"]) if a.get("column_b") else None

            session["answers"] = answers
            return session
        finally:
            cur.close()
            conn.close()

    def get_quiz_stats_summary(self) -> dict:
        """Thống kê tổng hợp tiến trình học tập."""
        conn = _get_conn()
        cur = conn.cursor(dictionary=True)
        try:
            cur.execute("SELECT COUNT(*) AS cnt FROM quiz_sessions WHERE completed_at IS NOT NULL")
            total_sessions = cur.fetchone()["cnt"]

            cur.execute("SELECT AVG(score/total*100) AS avg_score FROM quiz_sessions WHERE completed_at IS NOT NULL AND total > 0")
            row = cur.fetchone()
            avg_score = round(row["avg_score"], 1) if row["avg_score"] else 0

            cur.execute("SELECT SUM(time_spent_seconds) AS total_time FROM quiz_sessions WHERE completed_at IS NOT NULL")
            total_time = cur.fetchone()["total_time"] or 0

            # Điểm theo môn
            cur.execute("""
                SELECT e.subject, COUNT(*) AS attempts,
                       AVG(qs.score/qs.total*100) AS avg_score
                FROM quiz_sessions qs JOIN exams e ON qs.exam_id = e.id
                WHERE qs.completed_at IS NOT NULL AND qs.total > 0
                GROUP BY e.subject ORDER BY attempts DESC
            """)
            by_subject = cur.fetchall()

            # Xu hướng điểm (10 lần gần nhất)
            cur.execute("""
                SELECT qs.completed_at, qs.score, qs.total,
                       ROUND(qs.score/qs.total*100, 1) AS pct, e.subject
                FROM quiz_sessions qs JOIN exams e ON qs.exam_id = e.id
                WHERE qs.completed_at IS NOT NULL AND qs.total > 0
                ORDER BY qs.completed_at DESC LIMIT 200
            """)
            trend = cur.fetchall()

            return {
                "total_sessions": total_sessions,
                "avg_score": avg_score,
                "total_time": total_time,
                "by_subject": by_subject,
                "trend": trend,
            }
        finally:
            cur.close()
            conn.close()

    # ── Helper ────────────────────────────────────────────────

    @staticmethod
    def _row_to_exam_with_questions(row: dict, cur, conn) -> Exam:
        """Convert exam row + load questions qua exam_questions."""
        cur2 = conn.cursor(dictionary=True)
        cur2.execute("""
            SELECT q.* FROM questions q
            JOIN exam_questions eq ON q.id = eq.question_id
            WHERE eq.exam_id = %s
            ORDER BY eq.position
        """, (row["id"],))
        questions = [_row_to_question(r) for r in cur2.fetchall()]
        cur2.close()

        created = row.get("created_at")
        if created and not isinstance(created, str):
            created = created.isoformat() + "Z"

        return Exam(
            id=row["id"],
            title=row["title"],
            subject=row["subject"],
            difficulty=row["difficulty"],
            questions=questions,
            source_file=row.get("source_file"),
            created_at=created or "",
            grade=row.get("grade"),
            exam_code=row.get("exam_code"),
        )
