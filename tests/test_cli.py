"""集成测试与功能测试。

文件：test_cli.py
功能：通过模拟键盘输入驱动命令行完整流程，验证三类角色的业务闭环。
"""

from src import cli, db, scores, seed, students


def _feed(monkeypatch, values):
    """把给定的输入序列依次提供给 input()。"""
    pending = iter(values)
    monkeypatch.setattr("builtins.input", lambda *args: next(pending))


def test_init_command_creates_demo_data(tmp_path, capsys):
    """init 命令生成演示数据并可查询。"""
    db_file = tmp_path / "cli.db"
    assert cli.main(["init", "--db", str(db_file)]) == 0

    conn = db.connect(db_file)
    assert students.get_student(conn, "20230001")["name"] == "张三"
    assert len(scores.query_scores(conn)) == 5
    conn.close()
    assert "数据库已初始化" in capsys.readouterr().out


def test_admin_adds_student_via_menu(tmp_path, monkeypatch):
    """管理员通过菜单完成学生新增。"""
    db_file = tmp_path / "cli.db"
    conn = db.connect(db_file)
    seed.seed_demo(conn)
    conn.close()

    _feed(
        monkeypatch,
        [
            "admin", "Admin@123",
            "1", "1", "20239999", "赵六", "女", "计科2301", "", "", "",
            "0", "0", "",
        ],
    )
    assert cli.main(["run", "--db", str(db_file)]) == 0

    conn = db.connect(db_file)
    assert students.get_student(conn, "20239999")["name"] == "赵六"
    conn.close()


def test_teacher_records_score_and_views_report(tmp_path, monkeypatch, capsys):
    """教师录入成绩后生成班级报表。"""
    db_file = tmp_path / "cli.db"
    conn = db.connect(db_file)
    seed.seed_demo(conn)
    conn.close()

    _feed(
        monkeypatch,
        [
            "teacher1", "Teacher@123",
            "1", "20230003", "大学英语", "2025-2026-1", "66",
            "3", "计科2301", "", "",
            "0", "",
        ],
    )
    assert cli.main(["run", "--db", str(db_file)]) == 0

    output = capsys.readouterr().out
    assert "成绩已录入" in output
    assert "记录条数：4" in output

    conn = db.connect(db_file)
    rows = scores.query_scores(conn, sno="20230003", course="大学英语")
    assert rows[0]["score"] == 66.0
    conn.close()


def test_student_queries_own_scores(tmp_path, monkeypatch, capsys):
    """学生只能查看本人成绩。"""
    db_file = tmp_path / "cli.db"
    conn = db.connect(db_file)
    seed.seed_demo(conn)
    conn.close()

    _feed(monkeypatch, ["student1", "Student@123", "1", "0", ""])
    assert cli.main(["run", "--db", str(db_file)]) == 0

    output = capsys.readouterr().out
    assert "学号：20230001" in output
    assert "高等数学" in output
    assert "20230002" not in output
