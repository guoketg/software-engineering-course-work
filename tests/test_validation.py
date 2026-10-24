"""输入校验单元测试。

文件：test_validation.py
功能：以白盒方式覆盖学号、姓名、性别、联系方式、成绩、学期、账号等
      校验函数的分支。
"""

import pytest

from src import auth, scores, students
from src.errors import ValidationError


def test_sno_invalid():
    """学号过短或含非法字符均应被拒绝。"""
    with pytest.raises(ValidationError):
        students.validate_student("12345", "张三", "男", "计科2301")
    with pytest.raises(ValidationError):
        students.validate_student("2023-001", "张三", "男", "计科2301")


def test_name_empty():
    """姓名为空应被拒绝。"""
    with pytest.raises(ValidationError):
        students.validate_student("20230001", "  ", "男", "计科2301")


def test_gender_invalid():
    """性别不在取值范围内应被拒绝。"""
    with pytest.raises(ValidationError):
        students.validate_student("20230001", "张三", "未知", "计科2301")


def test_phone_invalid():
    """手机号格式错误应被拒绝。"""
    with pytest.raises(ValidationError):
        students.validate_student(
            "20230001", "张三", "男", "计科2301", phone="12345"
        )


def test_email_invalid():
    """邮箱格式错误应被拒绝。"""
    with pytest.raises(ValidationError):
        students.validate_student(
            "20230001", "张三", "男", "计科2301", email="zhangsan.example.com"
        )


def test_score_out_of_range():
    """低于 0 或高于 100 的成绩应被拒绝。"""
    with pytest.raises(ValidationError):
        scores.validate_score(-0.1)
    with pytest.raises(ValidationError):
        scores.validate_score(100.5)


def test_score_precision():
    """成绩超过一位小数应被拒绝。"""
    with pytest.raises(ValidationError):
        scores.validate_score(88.55)


def test_score_not_number():
    """非数字成绩应被拒绝。"""
    with pytest.raises(ValidationError):
        scores.validate_score("优秀")


def test_score_valid_boundary():
    """边界值 0 与 100 应通过校验，并返回浮点数。"""
    assert scores.validate_score(0) == 0.0
    assert scores.validate_score(100) == 100.0
    assert scores.validate_score("59.5") == 59.5


def test_term_invalid():
    """学期格式不合法应被拒绝。"""
    with pytest.raises(ValidationError):
        scores.validate_term("2025-2026-3")
    with pytest.raises(ValidationError):
        scores.validate_term("2025学年")


def test_course_empty():
    """课程名称为空应被拒绝。"""
    with pytest.raises(ValidationError):
        scores.validate_course("   ")


def test_password_too_short():
    """口令过短应被拒绝。"""
    with pytest.raises(ValidationError):
        auth.validate_account("tester", "123", "teacher", "测试教师")


def test_username_invalid():
    """用户名不符合命名规则应被拒绝。"""
    with pytest.raises(ValidationError):
        auth.validate_account("1abc", "123456", "teacher", "测试教师")


def test_role_invalid():
    """角色不在允许集合内应被拒绝。"""
    with pytest.raises(ValidationError):
        auth.validate_account("tester", "123456", "guest", "访客")
