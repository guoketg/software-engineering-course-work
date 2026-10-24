"""P1 学生信息管理单元测试。

文件：test_students.py
功能：覆盖学生新增、查询、修改、删除与列表过滤等主要分支。
"""

import pytest

from src import scores, students
from src.errors import DuplicateError, NotFoundError, ValidationError


def test_create_and_get_student(conn):
    """新增后可查询到完整信息。"""
    students.create_student(
        conn, "20231010", "赵六", "女", "计科2302", "计算机科学与技术",
        "13900000010", "zhaoliu@example.com",
    )
    student = students.get_student(conn, "20231010")
    assert student["name"] == "赵六"
    assert student["class_name"] == "计科2302"
    assert student["email"] == "zhaoliu@example.com"


def test_duplicate_sno_rejected(seeded):
    """重复学号应抛 DuplicateError。"""
    with pytest.raises(DuplicateError):
        students.create_student(seeded, "20230001", "重名", "男", "计科2301")


def test_update_student_fields(seeded):
    """修改字段后数据库内容同步更新。"""
    students.update_student(
        seeded, "20230001", phone="13800009999", class_name="计科2302"
    )
    student = students.get_student(seeded, "20230001")
    assert student["phone"] == "13800009999"
    assert student["class_name"] == "计科2302"


def test_update_missing_student(seeded):
    """修改不存在的学生应抛 NotFoundError。"""
    with pytest.raises(NotFoundError):
        students.update_student(seeded, "99999999", name="无名")


def test_delete_cascades_scores(conn):
    """删除学生时级联删除其成绩。"""
    students.create_student(conn, "20232020", "钱七", "男", "计科2303")
    scores.record_score(conn, "20232020", "高等数学", "2025-2026-1", 77)
    removed = students.delete_student(conn, "20232020")
    assert removed == 1
    assert students.get_student(conn, "20232020") is None
    assert scores.query_scores(conn, sno="20232020") == []


def test_delete_bound_account_rejected(seeded):
    """已绑定账号的学生不允许删除。"""
    with pytest.raises(ValidationError):
        students.delete_student(seeded, "20230001")


def test_list_students_filter(seeded):
    """按班级与关键字过滤学生列表，并返回去重班级名称。"""
    by_class = students.list_students(seeded, class_name="计科2301")
    assert [item["sno"] for item in by_class] == ["20230001", "20230002"]
    by_keyword = students.list_students(seeded, keyword="王")
    assert [item["sno"] for item in by_keyword] == ["20230003"]
    assert students.list_classes(seeded) == ["计科2301", "软工2301"]
