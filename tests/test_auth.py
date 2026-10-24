"""P3 用户权限管理单元测试。

文件：test_auth.py
功能：覆盖账号创建、身份认证、口令维护、启停用与角色权限校验分支。
"""

import pytest

from src import auth
from src.errors import (
    AccessDeniedError,
    AuthError,
    DuplicateError,
    ValidationError,
)


def test_authenticate_success(seeded):
    """正确口令登录成功，且数据库中不保存明文。"""
    user = auth.authenticate(seeded, "admin", "Admin@123")
    assert user.role == "admin"
    row = seeded.execute(
        "SELECT password_hash FROM users WHERE username = 'admin'"
    ).fetchone()
    assert row["password_hash"] != "Admin@123"


def test_duplicate_username(seeded):
    """重复用户名应抛 DuplicateError。"""
    with pytest.raises(DuplicateError):
        auth.create_user(seeded, "admin", "Admin@456", "admin", "另一个管理员")


def test_wrong_password(seeded):
    """口令错误应抛 AuthError。"""
    with pytest.raises(AuthError):
        auth.authenticate(seeded, "admin", "wrong-password")


def test_authenticate_missing_user(seeded):
    """账号不存在应抛 AuthError。"""
    with pytest.raises(AuthError):
        auth.authenticate(seeded, "nobody", "123456")


def test_inactive_account(seeded):
    """停用账号登录应被拒绝。"""
    auth.set_active(seeded, "teacher1", False)
    with pytest.raises(AuthError):
        auth.authenticate(seeded, "teacher1", "Teacher@123")


def test_change_password(seeded):
    """自助修改口令后旧口令失效、新口令可用。"""
    auth.change_password(seeded, "teacher1", "Teacher@123", "NewPass@1")
    with pytest.raises(AuthError):
        auth.authenticate(seeded, "teacher1", "Teacher@123")
    assert auth.authenticate(seeded, "teacher1", "NewPass@1").role == "teacher"


def test_reset_password(seeded):
    """管理员重置口令无需原口令。"""
    auth.reset_password(seeded, "teacher1", "Reset@123")
    assert auth.authenticate(seeded, "teacher1", "Reset@123").username == "teacher1"


def test_student_account_requires_existing_sno(seeded):
    """学生账号必须绑定存在的学号。"""
    with pytest.raises(ValidationError):
        auth.create_user(seeded, "student9", "Student@9", "student", "新生")
    with pytest.raises(ValidationError):
        auth.create_user(
            seeded, "student9", "Student@9", "student", "新生", "99999999"
        )


def test_require_role(seeded):
    """角色不匹配时抛 AccessDeniedError。"""
    student = auth.authenticate(seeded, "student1", "Student@123")
    auth.require_role(student, "student")
    with pytest.raises(AccessDeniedError):
        auth.require_role(student, "admin")


def test_list_users_filter(seeded):
    """按角色过滤账号列表，且不返回口令字段。"""
    teachers = auth.list_users(seeded, role="teacher")
    assert [item["username"] for item in teachers] == ["teacher1"]
    assert "password_hash" not in teachers[0]
