"""测试公共夹具。

文件：conftest.py
功能：为各测试模块提供临时数据库连接与预置数据。
"""

import pytest

from src import auth, db, students


@pytest.fixture()
def conn(tmp_path):
    """每个测试用例独立的临时数据库连接。"""
    connection = db.connect(tmp_path / "test.db")
    yield connection
    connection.close()


@pytest.fixture()
def seeded(conn):
    """预置三名学生与三类账号的连接。"""
    students.create_student(
        conn, "20230001", "张三", "男", "计科2301", "计算机科学与技术",
        "13800000001", "zhangsan@example.com",
    )
    students.create_student(
        conn, "20230002", "李四", "女", "计科2301", "计算机科学与技术",
        "13800000002", "lisi@example.com",
    )
    students.create_student(
        conn, "20230003", "王五", "男", "软工2301", "软件工程",
        "13800000003", "wangwu@example.com",
    )
    auth.create_user(conn, "admin", "Admin@123", "admin", "系统管理员")
    auth.create_user(conn, "teacher1", "Teacher@123", "teacher", "张老师")
    auth.create_user(conn, "student1", "Student@123", "student", "张三", "20230001")
    return conn
