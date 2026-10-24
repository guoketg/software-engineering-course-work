"""演示数据初始化。

文件：seed.py
功能：为首次运行的系统写入三名演示学生、三类演示账号与少量成绩，
      便于人工验证与功能测试。重复执行不会产生重复数据。
主要函数：seed_demo。
"""

import sqlite3

from . import auth, scores, students

# 演示学生：学号、姓名、性别、班级、专业、手机号、邮箱
DEMO_STUDENTS = (
    ("20230001", "张三", "男", "计科2301", "计算机科学与技术", "13800000001", "zhangsan@example.com"),
    ("20230002", "李四", "女", "计科2301", "计算机科学与技术", "13800000002", "lisi@example.com"),
    ("20230003", "王五", "男", "软工2301", "软件工程", "13800000003", "wangwu@example.com"),
)

# 演示账号：用户名、口令、角色、显示名称、绑定学号
DEMO_USERS = (
    ("admin", "Admin@123", "admin", "系统管理员", None),
    ("teacher1", "Teacher@123", "teacher", "张老师", None),
    ("student1", "Student@123", "student", "张三", "20230001"),
)

# 演示成绩：学号、课程、学期、成绩
DEMO_SCORES = (
    ("20230001", "高等数学", "2025-2026-1", 88.0),
    ("20230001", "大学英语", "2025-2026-1", 92.0),
    ("20230002", "高等数学", "2025-2026-1", 76.0),
    ("20230002", "大学英语", "2025-2026-1", 58.0),
    ("20230003", "高等数学", "2025-2026-1", 95.0),
)


def seed_demo(conn: sqlite3.Connection) -> None:
    """写入演示数据，已存在的数据跳过。"""
    for student in DEMO_STUDENTS:
        if students.get_student(conn, student[0]) is None:
            students.create_student(conn, *student)

    for username, password, role, display_name, student_sno in DEMO_USERS:
        exists = conn.execute(
            "SELECT 1 FROM users WHERE username = ?",
            (username,),
        ).fetchone()
        if exists is None:
            auth.create_user(conn, username, password, role, display_name, student_sno)

    for demo_score in DEMO_SCORES:
        existing = conn.execute(
            """
            SELECT 1 FROM scores
            JOIN students ON students.id = scores.student_id
            WHERE students.sno = ? AND scores.course = ? AND scores.term = ?
            """,
            (demo_score[0], demo_score[1], demo_score[2]),
        ).fetchone()
        if existing is None:
            scores.record_score(conn, *demo_score, recorded_by="teacher1")
