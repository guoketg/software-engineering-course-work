"""P3 用户权限管理。

文件：auth.py
功能：维护系统用户表，完成账号创建、身份认证、口令修改与重置、
      启停用以及角色权限校验。
主要函数：create_user、authenticate、change_password、reset_password、
          set_active、list_users、require_role。
"""

import re
import sqlite3
from dataclasses import dataclass

from . import config, security
from .errors import (
    AccessDeniedError,
    AuthError,
    DuplicateError,
    NotFoundError,
    ValidationError,
)

# 用户名：字母开头，3~20 位，允许字母、数字、下划线
USERNAME_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_]{2,19}$")


@dataclass(frozen=True)
class User:
    """登录用户快照，不包含口令信息。"""

    id: int
    username: str
    role: str
    display_name: str
    student_sno: str | None
    is_active: bool


def _row_to_user(row: sqlite3.Row) -> User:
    """把用户表记录转换为 User 对象。"""
    return User(
        id=row["id"],
        username=row["username"],
        role=row["role"],
        display_name=row["display_name"],
        student_sno=row["student_sno"],
        is_active=bool(row["is_active"]),
    )


def _validate_password(password: str) -> None:
    """校验口令长度。"""
    if not password or not (
        config.PASSWORD_MIN_LEN <= len(password) <= config.PASSWORD_MAX_LEN
    ):
        raise ValidationError(
            f"密码长度需为 {config.PASSWORD_MIN_LEN}~{config.PASSWORD_MAX_LEN} 位"
        )


def validate_account(username: str, password: str, role: str, display_name: str) -> None:
    """校验账号基础信息，失败时抛出 ValidationError。"""
    if not USERNAME_PATTERN.match(username or ""):
        raise ValidationError("用户名需以字母开头，长度 3~20，仅含字母、数字、下划线")
    _validate_password(password)
    if role not in config.VALID_ROLES:
        raise ValidationError("角色只能是 student、teacher 或 admin")
    if not (display_name or "").strip():
        raise ValidationError("显示名称不能为空")


def create_user(
    conn: sqlite3.Connection,
    username: str,
    password: str,
    role: str,
    display_name: str,
    student_sno: str | None = None,
) -> int:
    """新建系统账号，返回新账号编号。

    学生账号必须绑定已存在的学号；其他角色不允许绑定学号。
    """
    validate_account(username, password, role, display_name)

    if role == "student":
        if not student_sno:
            raise ValidationError("学生账号必须绑定学号")
        exists = conn.execute(
            "SELECT 1 FROM students WHERE sno = ?",
            (student_sno,),
        ).fetchone()
        if exists is None:
            raise ValidationError(f"绑定的学号 {student_sno} 不存在")
    elif student_sno:
        raise ValidationError("只有学生账号可以绑定学号")

    if conn.execute("SELECT 1 FROM users WHERE username = ?", (username,)).fetchone():
        raise DuplicateError(f"用户名 {username} 已存在")

    salt = security.make_salt()
    password_hash = security.hash_password(password, salt)
    cursor = conn.execute(
        """
        INSERT INTO users (username, password_hash, salt, role, display_name, student_sno)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (username, password_hash, salt, role, display_name.strip(), student_sno),
    )
    conn.commit()
    return cursor.lastrowid


def authenticate(conn: sqlite3.Connection, username: str, password: str) -> User:
    """校验用户名与口令，成功返回用户快照，失败抛出 AuthError。"""
    row = conn.execute(
        "SELECT * FROM users WHERE username = ?",
        (username or "",),
    ).fetchone()
    if row is None:
        raise AuthError("用户名或密码错误")
    if not security.verify_password(password or "", row["salt"], row["password_hash"]):
        raise AuthError("用户名或密码错误")
    if not row["is_active"]:
        raise AuthError("账号已停用，请联系管理员")
    return _row_to_user(row)


def _get_user_row(conn: sqlite3.Connection, username: str) -> sqlite3.Row:
    """按用户名取记录，不存在时抛 NotFoundError。"""
    row = conn.execute(
        "SELECT * FROM users WHERE username = ?",
        (username,),
    ).fetchone()
    if row is None:
        raise NotFoundError(f"账号 {username} 不存在")
    return row


def get_user(conn: sqlite3.Connection, username: str) -> User:
    """查询指定账号。"""
    return _row_to_user(_get_user_row(conn, username))


def change_password(
    conn: sqlite3.Connection,
    username: str,
    old_password: str,
    new_password: str,
) -> None:
    """用户自助修改口令，需要校验原口令。"""
    row = _get_user_row(conn, username)
    if not security.verify_password(old_password or "", row["salt"], row["password_hash"]):
        raise AuthError("原密码错误")
    _validate_password(new_password)
    _save_password(conn, row["id"], new_password)


def reset_password(conn: sqlite3.Connection, username: str, new_password: str) -> None:
    """管理员重置口令，不校验原口令。"""
    row = _get_user_row(conn, username)
    _validate_password(new_password)
    _save_password(conn, row["id"], new_password)


def _save_password(conn: sqlite3.Connection, user_id: int, new_password: str) -> None:
    """生成新盐并写入口令散列。"""
    salt = security.make_salt()
    password_hash = security.hash_password(new_password, salt)
    conn.execute(
        "UPDATE users SET password_hash = ?, salt = ? WHERE id = ?",
        (password_hash, salt, user_id),
    )
    conn.commit()


def set_active(conn: sqlite3.Connection, username: str, active: bool) -> None:
    """启用或停用账号。"""
    row = _get_user_row(conn, username)
    conn.execute(
        "UPDATE users SET is_active = ? WHERE id = ?",
        (1 if active else 0, row["id"]),
    )
    conn.commit()


def list_users(conn: sqlite3.Connection, role: str | None = None) -> list[dict]:
    """列出账号，可按角色过滤，不返回口令散列与盐。"""
    sql = (
        "SELECT id, username, role, display_name, student_sno, is_active "
        "FROM users"
    )
    params: tuple = ()
    if role:
        sql += " WHERE role = ?"
        params = (role,)
    sql += " ORDER BY role, username"
    return [dict(row) for row in conn.execute(sql, params).fetchall()]


def require_role(user: User, *roles: str) -> None:
    """校验用户角色是否在允许集合内，不允许时抛 AccessDeniedError。"""
    if user.role not in roles:
        allowed = "、".join(roles)
        raise AccessDeniedError(f"当前角色 {user.role} 无权执行该操作，需要角色：{allowed}")
