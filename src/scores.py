"""P2 成绩业务管理。

文件：scores.py
功能：读写成绩数据表，完成成绩录入（新增或覆盖）、按条件查询、
      删除以及班级成绩统计报表生成。
主要函数：record_score、query_scores、delete_score、class_report。
"""

import re
import sqlite3
from datetime import datetime

from . import config
from .errors import NotFoundError, ValidationError

# 学期格式：2025-2026-1 或 2025-2026-2
TERM_PATTERN = re.compile(r"^\d{4}-\d{4}-[12]$")

# 课程名称长度限制
COURSE_MAX_LEN = 50

# 查询结果列
SCORE_COLUMNS = (
    "students.sno AS sno, students.name AS name, students.class_name AS class_name, "
    "scores.course AS course, scores.term AS term, scores.score AS score"
)


def validate_course(course: str) -> None:
    """校验课程名称。"""
    if not (course or "").strip() or len(course.strip()) > COURSE_MAX_LEN:
        raise ValidationError(f"课程名称不能为空且不超过 {COURSE_MAX_LEN} 个字符")


def validate_term(term: str) -> None:
    """校验学期格式，例如 2025-2026-1。"""
    if not TERM_PATTERN.match(term or ""):
        raise ValidationError("学期格式应为 YYYY-YYYY-1 或 YYYY-YYYY-2，例如 2025-2026-1")


def validate_score(score) -> float:
    """校验成绩取值，允许 0~100 且最多一位小数，返回浮点值。"""
    try:
        value = float(score)
    except (TypeError, ValueError) as exc:
        raise ValidationError("成绩必须是数字") from exc
    if value < config.MIN_SCORE or value > config.MAX_SCORE:
        raise ValidationError("成绩必须在 0~100 之间")
    if round(value, 1) != value:
        raise ValidationError("成绩最多保留一位小数")
    return value


def record_score(
    conn: sqlite3.Connection,
    sno: str,
    course: str,
    term: str,
    score,
    recorded_by: str = "",
) -> str:
    """录入成绩。

    同一学生、课程、学期已存在记录时执行覆盖更新，返回 "created" 或 "updated"。
    """
    validate_course(course)
    validate_term(term)
    value = validate_score(score)

    student = conn.execute("SELECT id FROM students WHERE sno = ?", (sno,)).fetchone()
    if student is None:
        raise NotFoundError(f"学号 {sno} 不存在")

    existing = conn.execute(
        """
        SELECT id FROM scores
        WHERE student_id = ? AND course = ? AND term = ?
        """,
        (student["id"], course.strip(), term),
    ).fetchone()

    updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if existing is not None:
        conn.execute(
            "UPDATE scores SET score = ?, recorded_by = ?, updated_at = ? WHERE id = ?",
            (value, recorded_by, updated_at, existing["id"]),
        )
        action = "updated"
    else:
        conn.execute(
            """
            INSERT INTO scores (student_id, course, term, score, recorded_by, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (student["id"], course.strip(), term, value, recorded_by, updated_at),
        )
        action = "created"
    conn.commit()
    return action


def query_scores(
    conn: sqlite3.Connection,
    sno: str | None = None,
    class_name: str | None = None,
    course: str | None = None,
    term: str | None = None,
) -> list[dict]:
    """按学号、班级、课程、学期组合条件查询成绩。"""
    sql = f"""
        SELECT {SCORE_COLUMNS}
        FROM scores
        JOIN students ON students.id = scores.student_id
        WHERE 1 = 1
    """
    params: list = []
    if sno:
        sql += " AND students.sno = ?"
        params.append(sno)
    if class_name:
        sql += " AND students.class_name = ?"
        params.append(class_name)
    if course:
        sql += " AND scores.course = ?"
        params.append(course)
    if term:
        sql += " AND scores.term = ?"
        params.append(term)
    sql += " ORDER BY students.sno, scores.course, scores.term"
    return [dict(row) for row in conn.execute(sql, params).fetchall()]


def delete_score(conn: sqlite3.Connection, sno: str, course: str, term: str) -> None:
    """删除一条成绩记录。"""
    student = conn.execute("SELECT id FROM students WHERE sno = ?", (sno,)).fetchone()
    if student is None:
        raise NotFoundError(f"学号 {sno} 不存在")

    cursor = conn.execute(
        """
        DELETE FROM scores
        WHERE student_id = ? AND course = ? AND term = ?
        """,
        (student["id"], course, term),
    )
    if cursor.rowcount == 0:
        raise NotFoundError(f"未找到 {sno} 在 {term} 的 {course} 成绩")
    conn.commit()


def score_bucket(score: float) -> str:
    """把成绩映射到统计分数段。"""
    if score >= 90:
        return "90-100"
    if score >= 80:
        return "80-89"
    if score >= 70:
        return "70-79"
    if score >= 60:
        return "60-69"
    return "<60"


def class_report(
    conn: sqlite3.Connection,
    class_name: str,
    course: str | None = None,
    term: str | None = None,
) -> dict:
    """生成班级成绩统计报表。

    返回记录条数、平均分、最高分、最低分、及格人数、及格率与分数段分布。
    """
    if not (class_name or "").strip():
        raise ValidationError("班级不能为空")

    rows = query_scores(conn, class_name=class_name, course=course, term=term)
    report = {
        "class_name": class_name,
        "course": course or "全部课程",
        "term": term or "全部学期",
        "count": len(rows),
        "average": 0.0,
        "highest": 0.0,
        "lowest": 0.0,
        "pass_count": 0,
        "pass_rate": 0.0,
        "distribution": {bucket: 0 for bucket in config.DISTRIBUTION_BUCKETS},
    }
    if not rows:
        return report

    values = [row["score"] for row in rows]
    pass_count = sum(1 for value in values if value >= config.PASS_SCORE)
    for value in values:
        report["distribution"][score_bucket(value)] += 1

    report["average"] = round(sum(values) / len(values), 1)
    report["highest"] = max(values)
    report["lowest"] = min(values)
    report["pass_count"] = pass_count
    report["pass_rate"] = round(pass_count * 100 / len(values), 1)
    return report
