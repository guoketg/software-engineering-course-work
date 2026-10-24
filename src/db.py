"""数据库连接与物理表结构。

文件：db.py
功能：创建 SQLite 连接、打开外键约束、执行建表与索引语句。
      物理设计说明见 docs/实验三_系统实现报告.md。
"""

import sqlite3
from pathlib import Path

from . import config

# 物理表结构：学生基本信息表、系统用户表、成绩数据表
SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS students (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    sno        TEXT    NOT NULL UNIQUE,
    name       TEXT    NOT NULL,
    gender     TEXT    NOT NULL,
    class_name TEXT    NOT NULL,
    major      TEXT    NOT NULL DEFAULT '',
    phone      TEXT    NOT NULL DEFAULT '',
    email      TEXT    NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT    NOT NULL UNIQUE,
    password_hash TEXT    NOT NULL,
    salt          TEXT    NOT NULL,
    role          TEXT    NOT NULL,
    display_name  TEXT    NOT NULL,
    student_sno   TEXT,
    is_active     INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS scores (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id  INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    course      TEXT    NOT NULL,
    term        TEXT    NOT NULL,
    score       REAL    NOT NULL CHECK (score >= 0 AND score <= 100),
    recorded_by TEXT    NOT NULL DEFAULT '',
    updated_at  TEXT    NOT NULL,
    UNIQUE (student_id, course, term)
);

CREATE INDEX IF NOT EXISTS idx_students_class ON students(class_name);
CREATE INDEX IF NOT EXISTS idx_scores_course ON scores(course, term);
"""


def connect(db_path: str | Path | None = None) -> sqlite3.Connection:
    """建立数据库连接并初始化表结构。

    db_path 为空时使用 config.DB_PATH；传入 ":memory:" 时使用内存数据库。
    """
    if db_path is None:
        path = Path(config.DB_PATH)
        path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(path))
    elif str(db_path) == ":memory:":
        conn = sqlite3.connect(":memory:")
    else:
        path = Path(db_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(path))

    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    init_db(conn)
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    """执行建表与索引语句，重复执行安全。"""
    conn.executescript(SCHEMA_SQL)
    conn.commit()
