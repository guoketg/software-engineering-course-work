"""命令行界面。

文件：cli.py
功能：提供登录入口与三角色菜单，串联 P1~P4 业务模块。
      运行方式：
        python -m src.main            进入交互菜单
        python -m src.main init       初始化数据库并写入演示数据
主要函数：main、run_menu。
"""

import argparse
import sqlite3

from . import auth, backup, config, db, report, scores, seed, students
from .errors import AppError

MENU_LINE = "-" * 60
TITLE_LINE = "=" * 60


def _ask(prompt: str) -> str:
    """读取一行输入并去除首尾空白。"""
    return input(prompt).strip()


def _ask_optional(prompt: str, current: str) -> str:
    """读取一行输入，直接回车时保留原值。"""
    value = _ask(prompt)
    return value if value else current


def _ask_float(prompt: str) -> float:
    """读取成绩输入，非数字时抛出 ValidationError。"""
    value = _ask(prompt)
    return scores.validate_score(value)


def _print_table(headers, rows) -> None:
    """打印查询结果表格。"""
    print(report.format_table(headers, rows))


def _score_rows(rows: list[dict], with_student: bool = True) -> list[tuple]:
    """把成绩查询结果转换为表格行。"""
    if with_student:
        return [
            (
                row["sno"],
                row["name"],
                row["class_name"],
                row["course"],
                row["term"],
                row["score"],
            )
            for row in rows
        ]
    return [(row["course"], row["term"], row["score"]) for row in rows]


def main(argv=None) -> int:
    """程序入口，返回进程退出码。"""
    parser = argparse.ArgumentParser(
        prog="student-score-system",
        description="学生成绩管理系统命令行界面",
    )
    parser.add_argument(
        "command",
        nargs="?",
        default="run",
        choices=("run", "init"),
        help="run 进入菜单，init 初始化演示数据",
    )
    parser.add_argument("--db", dest="db_path", default=None, help="数据库文件路径")
    args = parser.parse_args(argv)

    conn = db.connect(args.db_path)
    try:
        if args.command == "init":
            seed.seed_demo(conn)
            print(f"数据库已初始化：{args.db_path or config.DB_PATH}")
            print("演示账号：admin/Admin@123、teacher1/Teacher@123、student1/Student@123")
            return 0
        return run_menu(conn)
    finally:
        conn.close()


def run_menu(conn: sqlite3.Connection) -> int:
    """登录循环，按角色进入对应菜单。"""
    print(TITLE_LINE)
    print("学生成绩管理系统（命令行版）")
    print(TITLE_LINE)
    while True:
        username = _ask("用户名（输入空行退出）：")
        if not username:
            print("再见。")
            return 0
        password = input("密码：")
        try:
            user = auth.authenticate(conn, username, password)
        except AppError as exc:
            print(f"登录失败：{exc}")
            continue

        print(f"登录成功：{user.display_name}（角色：{user.role}）")
        if user.role == "admin":
            _admin_menu(conn, user)
        elif user.role == "teacher":
            _teacher_menu(conn, user)
        else:
            _student_menu(conn, user)
        print("已退出当前账号。")


def _change_password(conn: sqlite3.Connection, user: auth.User) -> None:
    """修改当前用户口令。"""
    old_password = input("原密码：")
    new_password = input("新密码：")
    confirm = input("确认新密码：")
    if new_password != confirm:
        print("两次输入的新密码不一致")
        return
    auth.change_password(conn, user.username, old_password, new_password)
    print("密码已修改")


def _admin_menu(conn: sqlite3.Connection, user: auth.User) -> None:
    """管理员菜单，覆盖 P1~P4 四个模块。"""
    while True:
        print(MENU_LINE)
        print("管理员菜单")
        print("  1 学生信息管理")
        print("  2 成绩业务管理")
        print("  3 用户权限管理")
        print("  4 数据集备份与恢复")
        print("  5 修改密码")
        print("  0 退出登录")
        choice = _ask("请选择：")
        try:
            if choice == "0":
                return
            if choice == "1":
                _admin_student_menu(conn)
            elif choice == "2":
                _admin_score_menu(conn)
            elif choice == "3":
                _admin_user_menu(conn)
            elif choice == "4":
                _backup_menu(conn)
            elif choice == "5":
                _change_password(conn, user)
            else:
                print("无效选项")
        except AppError as exc:
            print(f"操作失败：{exc}")


def _admin_student_menu(conn: sqlite3.Connection) -> None:
    """P1 学生信息管理子菜单。"""
    while True:
        print(MENU_LINE)
        print("学生信息管理：1 新增  2 修改  3 删除  4 查询  5 列表  0 返回")
        choice = _ask("请选择：")
        try:
            if choice == "0":
                return
            if choice == "1":
                sno = _ask("学号：")
                name = _ask("姓名：")
                gender = _ask("性别（男/女）：")
                class_name = _ask("班级：")
                major = _ask("专业（可空）：")
                phone = _ask("手机号（可空）：")
                email = _ask("邮箱（可空）：")
                students.create_student(
                    conn, sno, name, gender, class_name, major, phone, email
                )
                print(f"已新增学生 {sno} {name}")
            elif choice == "2":
                sno = _ask("要修改的学号：")
                current = students.require_student(conn, sno)
                name = _ask_optional(f"姓名[{current['name']}]：", current["name"])
                gender = _ask_optional(f"性别[{current['gender']}]：", current["gender"])
                class_name = _ask_optional(
                    f"班级[{current['class_name']}]：", current["class_name"]
                )
                major = _ask_optional(f"专业[{current['major']}]：", current["major"])
                phone = _ask_optional(f"手机号[{current['phone']}]：", current["phone"])
                email = _ask_optional(f"邮箱[{current['email']}]：", current["email"])
                students.update_student(
                    conn,
                    sno,
                    name=name,
                    gender=gender,
                    class_name=class_name,
                    major=major,
                    phone=phone,
                    email=email,
                )
                print(f"已修改学生 {sno}")
            elif choice == "3":
                sno = _ask("要删除的学号：")
                removed = students.delete_student(conn, sno)
                print(f"已删除学生 {sno}，同时删除成绩 {removed} 条")
            elif choice == "4":
                sno = _ask("学号：")
                current = students.require_student(conn, sno)
                _print_table(
                    ("学号", "姓名", "性别", "班级", "专业", "手机号", "邮箱"),
                    [
                        (
                            current["sno"],
                            current["name"],
                            current["gender"],
                            current["class_name"],
                            current["major"],
                            current["phone"],
                            current["email"],
                        )
                    ],
                )
            elif choice == "5":
                class_name = _ask("班级（可空表示全部）：")
                keyword = _ask("关键字（学号或姓名，可空）：")
                rows = students.list_students(
                    conn,
                    class_name=class_name or None,
                    keyword=keyword or None,
                )
                _print_table(
                    ("学号", "姓名", "性别", "班级", "专业"),
                    [
                        (
                            row["sno"],
                            row["name"],
                            row["gender"],
                            row["class_name"],
                            row["major"],
                        )
                        for row in rows
                    ],
                )
            else:
                print("无效选项")
        except AppError as exc:
            print(f"操作失败：{exc}")


def _admin_score_menu(conn: sqlite3.Connection) -> None:
    """P2 成绩业务管理子菜单。"""
    while True:
        print(MENU_LINE)
        print("成绩业务管理：1 录入成绩  2 查询成绩  3 删除成绩  4 班级报表  0 返回")
        choice = _ask("请选择：")
        try:
            if choice == "0":
                return
            if choice == "1":
                sno = _ask("学号：")
                course = _ask("课程：")
                term = _ask("学期（如 2025-2026-1）：")
                value = _ask_float("成绩：")
                action = scores.record_score(conn, sno, course, term, value, recorded_by="admin")
                print(f"成绩已{'更新' if action == 'updated' else '录入'}：{sno} {course} {value}")
            elif choice == "2":
                sno = _ask("学号（可空）：")
                class_name = _ask("班级（可空）：")
                course = _ask("课程（可空）：")
                term = _ask("学期（可空）：")
                rows = scores.query_scores(
                    conn,
                    sno=sno or None,
                    class_name=class_name or None,
                    course=course or None,
                    term=term or None,
                )
                _print_table(
                    ("学号", "姓名", "班级", "课程", "学期", "成绩"),
                    _score_rows(rows),
                )
            elif choice == "3":
                sno = _ask("学号：")
                course = _ask("课程：")
                term = _ask("学期：")
                scores.delete_score(conn, sno, course, term)
                print(f"已删除 {sno} 的 {course}（{term}）成绩")
            elif choice == "4":
                class_name = _ask("班级：")
                course = _ask("课程（可空表示全部）：")
                term = _ask("学期（可空表示全部）：")
                result = scores.class_report(
                    conn,
                    class_name,
                    course=course or None,
                    term=term or None,
                )
                print(report.format_class_report(result))
            else:
                print("无效选项")
        except AppError as exc:
            print(f"操作失败：{exc}")


def _admin_user_menu(conn: sqlite3.Connection) -> None:
    """P3 用户权限管理子菜单。"""
    while True:
        print(MENU_LINE)
        print("用户权限管理：1 新建账号  2 重置密码  3 启用/停用  4 账号列表  0 返回")
        choice = _ask("请选择：")
        try:
            if choice == "0":
                return
            if choice == "1":
                username = _ask("用户名：")
                password = input("初始密码：")
                role = _ask("角色（student/teacher/admin）：")
                display_name = _ask("显示名称：")
                student_sno = None
                if role == "student":
                    student_sno = _ask("绑定学号：")
                auth.create_user(conn, username, password, role, display_name, student_sno)
                print(f"已创建账号 {username}")
            elif choice == "2":
                username = _ask("用户名：")
                new_password = input("新密码：")
                auth.reset_password(conn, username, new_password)
                print(f"已重置 {username} 的密码")
            elif choice == "3":
                username = _ask("用户名：")
                action = _ask("输入 1 启用，输入 0 停用：")
                auth.set_active(conn, username, action == "1")
                print(f"账号 {username} 已{'启用' if action == '1' else '停用'}")
            elif choice == "4":
                role = _ask("角色过滤（可空）：")
                rows = auth.list_users(conn, role=role or None)
                _print_table(
                    ("用户名", "角色", "显示名称", "绑定学号", "状态"),
                    [
                        (
                            row["username"],
                            row["role"],
                            row["display_name"],
                            row["student_sno"] or "",
                            "启用" if row["is_active"] else "停用",
                        )
                        for row in rows
                    ],
                )
            else:
                print("无效选项")
        except AppError as exc:
            print(f"操作失败：{exc}")


def _backup_menu(conn: sqlite3.Connection) -> None:
    """P4 数据集备份与恢复子菜单。"""
    while True:
        print(MENU_LINE)
        print("数据集备份与恢复：1 创建备份  2 备份列表  3 恢复备份  0 返回")
        choice = _ask("请选择：")
        try:
            if choice == "0":
                return
            if choice == "1":
                path = backup.create_backup(conn)
                print(f"备份完成：{path.name}")
            elif choice == "2":
                items = backup.list_backups()
                _print_table(
                    ("备份文件", "大小(字节)", "修改时间"),
                    [(item["name"], item["size"], item["modified"]) for item in items],
                )
            elif choice == "3":
                items = backup.list_backups()
                _print_table(
                    ("备份文件", "大小(字节)", "修改时间"),
                    [(item["name"], item["size"], item["modified"]) for item in items],
                )
                name = _ask("要恢复的备份文件名：")
                path = backup.restore_backup(conn, config.BACKUP_DIR / name)
                print(f"已从 {path.name} 恢复数据库")
            else:
                print("无效选项")
        except AppError as exc:
            print(f"操作失败：{exc}")


def _teacher_menu(conn: sqlite3.Connection, user: auth.User) -> None:
    """教师菜单：录入成绩、查询成绩、班级报表。"""
    while True:
        print(MENU_LINE)
        print("教师菜单：1 录入成绩  2 查询成绩  3 班级成绩报表  4 修改密码  0 退出")
        choice = _ask("请选择：")
        try:
            if choice == "0":
                return
            if choice == "1":
                sno = _ask("学号：")
                course = _ask("课程：")
                term = _ask("学期（如 2025-2026-1）：")
                value = _ask_float("成绩：")
                action = scores.record_score(
                    conn, sno, course, term, value, recorded_by=user.username
                )
                print(f"成绩已{'更新' if action == 'updated' else '录入'}：{sno} {course} {value}")
            elif choice == "2":
                sno = _ask("学号（可空）：")
                class_name = _ask("班级（可空）：")
                course = _ask("课程（可空）：")
                rows = scores.query_scores(
                    conn,
                    sno=sno or None,
                    class_name=class_name or None,
                    course=course or None,
                )
                _print_table(
                    ("学号", "姓名", "班级", "课程", "学期", "成绩"),
                    _score_rows(rows),
                )
            elif choice == "3":
                class_name = _ask("班级：")
                course = _ask("课程（可空表示全部）：")
                term = _ask("学期（可空表示全部）：")
                result = scores.class_report(
                    conn,
                    class_name,
                    course=course or None,
                    term=term or None,
                )
                print(report.format_class_report(result))
            elif choice == "4":
                _change_password(conn, user)
            else:
                print("无效选项")
        except AppError as exc:
            print(f"操作失败：{exc}")


def _student_menu(conn: sqlite3.Connection, user: auth.User) -> None:
    """学生菜单：查询个人成绩、修改密码。"""
    while True:
        print(MENU_LINE)
        print("学生菜单：1 查询我的成绩  2 修改密码  0 退出")
        choice = _ask("请选择：")
        try:
            if choice == "0":
                return
            if choice == "1":
                if not user.student_sno:
                    print("当前账号未绑定学号，请联系管理员")
                    continue
                student = students.require_student(conn, user.student_sno)
                print(
                    f"学号：{student['sno']}  姓名：{student['name']}"
                    f"  班级：{student['class_name']}"
                )
                rows = scores.query_scores(conn, sno=user.student_sno)
                _print_table(
                    ("课程", "学期", "成绩"),
                    _score_rows(rows, with_student=False),
                )
            elif choice == "2":
                _change_password(conn, user)
            else:
                print("无效选项")
        except AppError as exc:
            print(f"操作失败：{exc}")
