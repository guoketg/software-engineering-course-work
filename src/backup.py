"""P4 数据集备份与恢复。

文件：backup.py
功能：读写系统备份文件，实现数据库备份、备份清单查询与故障后恢复。
主要函数：create_backup、list_backups、restore_backup。
"""

import sqlite3
from datetime import datetime
from pathlib import Path

from . import config
from .errors import BackupError, NotFoundError


def _resolve_dir(backup_dir: str | Path | None) -> Path:
    """返回备份目录并确保其存在。"""
    directory = Path(backup_dir) if backup_dir else Path(config.BACKUP_DIR)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def create_backup(conn: sqlite3.Connection, backup_dir: str | Path | None = None) -> Path:
    """使用 SQLite 在线备份接口生成备份文件，返回备份文件路径。"""
    directory = _resolve_dir(backup_dir)
    filename = f"school_{datetime.now():%Y%m%d_%H%M%S_%f}.db"
    target = directory / filename

    conn.commit()
    destination = sqlite3.connect(str(target))
    try:
        conn.backup(destination)
    finally:
        destination.close()
    return target


def list_backups(backup_dir: str | Path | None = None) -> list[dict]:
    """列出备份文件，按时间倒序返回名称、路径、大小与修改时间。"""
    directory = Path(backup_dir) if backup_dir else Path(config.BACKUP_DIR)
    if not directory.exists():
        return []

    items = []
    for path in sorted(directory.glob("school_*.db"), reverse=True):
        stat = path.stat()
        items.append(
            {
                "name": path.name,
                "path": path,
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
            }
        )
    return items


def restore_backup(conn: sqlite3.Connection, backup_path: str | Path) -> Path:
    """从备份文件恢复数据库，恢复前执行完整性校验。"""
    path = Path(backup_path)
    if not path.exists():
        raise NotFoundError(f"备份文件不存在：{path}")

    source = sqlite3.connect(str(path))
    try:
        result = source.execute("PRAGMA integrity_check").fetchone()
        if not result or result[0] != "ok":
            raise BackupError("备份文件完整性校验失败，拒绝恢复")
        conn.commit()
        source.backup(conn)
    except sqlite3.DatabaseError as exc:
        raise BackupError(f"备份文件无法读取：{exc}") from exc
    finally:
        source.close()
    return path
