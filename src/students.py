"""P1 学生信息管理。

文件：students.py
功能：操作学生基本信息表，完成学生信息增加、删除、修改、查询。
主要函数：create_student、update_student、delete_student、
          get_student、list_students、list_classes。
"""

import re
import sqlite3

from . import config
from .errors import DuplicateError, NotFoundError, ValidationError

# 学号：6~20 位字母或数字
SNO_PATTERN = re.compile(r"^[A-Za-z0-9]{6,20}$")

# 手机号：1 开头的 11 位数字
PHONE_PATTERN = re.compile(r"^1\d{10}$")

# 邮箱：简单合法性校验
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# 各字段长度限制
NAME_MAX_LEN = 20
CLASS_MAX_LEN = 30
MAJOR_MAX_LEN = 40

# 允许修改的字段
STUDENT_FIELDS = ("name", "gender", "class_name", "major", "phone", "email")

# 查询列表使用的列
STUDENT_COLUMNS = (
    "sno, name, gender, class_name, major, phone, email"
)


def validate_student(
    sno: str,
    name: str,
    gender: str,
    class_name: str,
    major: str = "",
    phone: str = "",
    email: str = "",
) -> None:
    """校验学生信息，失败时抛出 ValidationError。"""
    if not SNO_PATTERN.match(sno or ""):
        raise ValidationError(
            f"学号需为 {config.SNO_MIN_LEN}~{config.SNO_MAX_LEN} 位字母或数字"
        )
    if not (name or "").strip() or len(name.strip()) > NAME_MAX_LEN:
        raise ValidationError(f"姓名不能为空且不超过 {NAME_MAX_LEN} 个字符")
    if gender not in config.VALID_GENDERS:
        raise ValidationError("性别只能是 男 或 女")
    if not (class_name or "").strip() or len(class_name.strip()) > CLASS_MAX_LEN:
        raise ValidationError(f"班级不能为空且不超过 {CLASS_MAX_LEN} 个字符")
    if len(major or "") > MAJOR_MAX_LEN:
        raise ValidationError(f"专业名称不超过 {MAJOR_MAX_LEN} 个字符")
    if phone and not PHONE_PATTERN.match(phone):
        raise ValidationError("手机号需为 1 开头的 11 位数字")
    if email and not EMAIL_PATTERN.match(email):
        raise ValidationError("邮箱格式不正确")


def create_student(
    conn: sqlite3.Connection,
    sno: str,
    name: str,
    gender: str,
    class_name: str,
    major: str = "",
    phone: str = "",
    email: str = "",
) -> int:
    """新增学生记录，返回新记录编号。"""
    validate_student(sno, name, gender, class_name, major, phone, email)
    if conn.execute("SELECT 1 FROM students WHERE sno = ?", (sno,)).fetchone():
        raise DuplicateError(f"学号 {sno} 已存在")

    cursor = conn.execute(
        """
        INSERT INTO students (sno, name, gender, class_name, major, phone, email)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (sno, name.strip(), gender, class_name.strip(), major.strip(), phone, email),
    )
    conn.commit()
    return cursor.lastrowid


def update_student(conn: sqlite3.Connection, sno: str, **changes) -> None:
    """修改学生信息，只允许修改 STUDENT_FIELDS 中的字段。"""
    unknown = set(changes) - set(STUDENT_FIELDS)
    if unknown:
        raise ValidationError(f"不支持修改字段：{'、'.join(sorted(unknown))}")

    current = get_student(conn, sno)
    if current is None:
        raise NotFoundError(f"学号 {sno} 不存在")

    merged = {
        "name": changes.get("name", current["name"]),
        "gender": changes.get("gender", current["gender"]),
        "class_name": changes.get("class_name", current["class_name"]),
        "major": changes.get("major", current["major"]),
        "phone": changes.get("phone", current["phone"]),
        "email": changes.get("email", current["email"]),
    }
    validate_student(
        sno,
        merged["name"],
        merged["gender"],
        merged["class_name"],
        merged["major"],
        merged["phone"],
        merged["email"],
    )

    conn.execute(
        """
        UPDATE students
        SET name = ?, gender = ?, class_name = ?, major = ?, phone = ?, email = ?
        WHERE sno = ?
        """,
        (
            merged["name"].strip(),
            merged["gender"],
            merged["class_name"].strip(),
            merged["major"].strip(),
            merged["phone"],
            merged["email"],
            sno,
        ),
    )
    conn.commit()


def delete_student(conn: sqlite3.Connection, sno: str) -> int:
    """删除学生及其成绩记录，返回被级联删除的成绩条数。

    若该学号已绑定系统账号，则拒绝删除，避免产生孤立账号。
    """
    row = conn.execute("SELECT id FROM students WHERE sno = ?", (sno,)).fetchone()
    if row is None:
        raise NotFoundError(f"学号 {sno} 不存在")

    bound = conn.execute(
        "SELECT username FROM users WHERE student_sno = ?",
        (sno,),
    ).fetchone()
    if bound is not None:
        raise ValidationError(f"学号 {sno} 已绑定账号 {bound['username']}，请先解绑或删除该账号")

    score_count = conn.execute(
        "SELECT COUNT(*) FROM scores WHERE student_id = ?",
        (row["id"],),
    ).fetchone()[0]

    conn.execute("DELETE FROM students WHERE id = ?", (row["id"],))
    conn.commit()
    return score_count


def get_student(conn: sqlite3.Connection, sno: str) -> dict | None:
    """按学号查询单个学生，不存在时返回 None。"""
    row = conn.execute(
        f"SELECT {STUDENT_COLUMNS} FROM students WHERE sno = ?",
        (sno,),
    ).fetchone()
    return dict(row) if row is not None else None


def require_student(conn: sqlite3.Connection, sno: str) -> dict:
    """按学号取学生，不存在时抛 NotFoundError。"""
    student = get_student(conn, sno)
    if student is None:
        raise NotFoundError(f"学号 {sno} 不存在")
    return student


def list_students(
    conn: sqlite3.Connection,
    class_name: str | None = None,
    keyword: str | None = None,
) -> list[dict]:
    """按班级与关键字（学号或姓名）过滤查询学生列表。"""
    sql = f"SELECT {STUDENT_COLUMNS} FROM students WHERE 1 = 1"
    params: list = []
    if class_name:
        sql += " AND class_name = ?"
        params.append(class_name)
    if keyword:
        sql += " AND (sno LIKE ? OR name LIKE ?)"
        like = f"%{keyword}%"
        params.extend([like, like])
    sql += " ORDER BY sno"
    return [dict(row) for row in conn.execute(sql, params).fetchall()]


def list_classes(conn: sqlite3.Connection) -> list[str]:
    """返回现有全部班级名称，用于下拉选择。"""
    rows = conn.execute(
        "SELECT DISTINCT class_name FROM students ORDER BY class_name"
    ).fetchall()
    return [row["class_name"] for row in rows]
