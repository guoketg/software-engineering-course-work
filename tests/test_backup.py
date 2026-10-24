"""P4 数据集备份与恢复单元测试。

文件：test_backup.py
功能：覆盖备份生成、清单查询、恢复成功及损坏/缺失备份的异常分支。
"""

import pytest

from src import backup, students
from src.errors import BackupError, NotFoundError


def test_create_backup(seeded, tmp_path):
    """备份文件生成且可独立打开并包含数据。"""
    path = backup.create_backup(seeded, tmp_path / "backups")
    assert path.exists()
    assert path.name.startswith("school_")
    assert path.stat().st_size > 0


def test_list_backups(seeded, tmp_path):
    """备份清单按时间倒序返回。"""
    directory = tmp_path / "backups"
    first = backup.create_backup(seeded, directory)
    second = backup.create_backup(seeded, directory)
    names = [item["name"] for item in backup.list_backups(directory)]
    assert names == [second.name, first.name]
    assert all(item["size"] > 0 for item in backup.list_backups(directory))


def test_restore_after_delete(seeded, tmp_path):
    """恢复备份后，删除前写入的学生数据重新可见。"""
    students.create_student(seeded, "20233030", "孙八", "女", "计科2304")
    path = backup.create_backup(seeded, tmp_path / "backups")
    students.delete_student(seeded, "20233030")
    assert students.get_student(seeded, "20233030") is None

    backup.restore_backup(seeded, path)
    assert students.get_student(seeded, "20233030")["name"] == "孙八"


def test_restore_corrupt_backup(seeded, tmp_path):
    """损坏的备份文件应抛 BackupError。"""
    bad_file = tmp_path / "school_bad.db"
    bad_file.write_bytes(b"this is not a sqlite database")
    with pytest.raises(BackupError):
        backup.restore_backup(seeded, bad_file)


def test_restore_missing_backup(seeded, tmp_path):
    """备份文件不存在应抛 NotFoundError。"""
    with pytest.raises(NotFoundError):
        backup.restore_backup(seeded, tmp_path / "school_none.db")
