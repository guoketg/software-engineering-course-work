"""P2 成绩业务管理单元测试。

文件：test_scores.py
功能：覆盖成绩录入（新增与覆盖）、条件查询、删除与班级统计报表分支。
"""

import pytest

from src import scores
from src.errors import NotFoundError, ValidationError


def test_record_creates_score(seeded):
    """首次录入返回 created 并可查询到记录。"""
    action = scores.record_score(
        seeded, "20230001", "高等数学", "2025-2026-1", 88, recorded_by="teacher1"
    )
    assert action == "created"
    rows = scores.query_scores(seeded, sno="20230001")
    assert len(rows) == 1
    assert rows[0]["score"] == 88.0
    assert rows[0]["name"] == "张三"


def test_record_updates_same_key(seeded):
    """同一学生课程学期重复录入时覆盖更新。"""
    scores.record_score(seeded, "20230001", "高等数学", "2025-2026-1", 70)
    action = scores.record_score(
        seeded, "20230001", "高等数学", "2025-2026-1", 90
    )
    assert action == "updated"
    rows = scores.query_scores(seeded, sno="20230001", course="高等数学")
    assert len(rows) == 1
    assert rows[0]["score"] == 90.0


def test_record_unknown_student(seeded):
    """学号不存在时抛 NotFoundError。"""
    with pytest.raises(NotFoundError):
        scores.record_score(seeded, "99999999", "高等数学", "2025-2026-1", 80)


def test_record_invalid_score(seeded):
    """成绩越界时抛 ValidationError。"""
    with pytest.raises(ValidationError):
        scores.record_score(seeded, "20230001", "高等数学", "2025-2026-1", 120)


def test_query_filters(seeded):
    """按学号、班级、课程、学期组合过滤查询。"""
    scores.record_score(seeded, "20230001", "高等数学", "2025-2026-1", 88)
    scores.record_score(seeded, "20230001", "大学英语", "2025-2026-1", 92)
    scores.record_score(seeded, "20230002", "高等数学", "2025-2026-1", 76)
    scores.record_score(seeded, "20230003", "高等数学", "2025-2026-2", 95)

    assert len(scores.query_scores(seeded)) == 4
    assert len(scores.query_scores(seeded, class_name="计科2301")) == 3
    assert len(scores.query_scores(seeded, course="高等数学")) == 3
    assert len(scores.query_scores(seeded, term="2025-2026-2")) == 1
    assert len(scores.query_scores(seeded, sno="20230001")) == 2


def test_class_report_statistics(seeded):
    """班级报表统计平均分、极值、及格率与分数段分布。"""
    scores.record_score(seeded, "20230001", "高等数学", "2025-2026-1", 88)
    scores.record_score(seeded, "20230001", "大学英语", "2025-2026-1", 92)
    scores.record_score(seeded, "20230002", "高等数学", "2025-2026-1", 76)
    scores.record_score(seeded, "20230002", "大学英语", "2025-2026-1", 58)

    report = scores.class_report(seeded, "计科2301")
    assert report["count"] == 4
    assert report["average"] == 78.5
    assert report["highest"] == 92
    assert report["lowest"] == 58
    assert report["pass_count"] == 3
    assert report["pass_rate"] == 75.0
    assert report["distribution"] == {
        "90-100": 1,
        "80-89": 1,
        "70-79": 1,
        "60-69": 0,
        "<60": 1,
    }


def test_class_report_empty(seeded):
    """无成绩的班级返回全零统计。"""
    report = scores.class_report(seeded, "软工2301")
    assert report["count"] == 0
    assert report["average"] == 0.0
    assert report["pass_rate"] == 0.0
    assert all(count == 0 for count in report["distribution"].values())


def test_score_bucket_boundaries():
    """分数段边界值归属正确。"""
    assert scores.score_bucket(90) == "90-100"
    assert scores.score_bucket(89.9) == "80-89"
    assert scores.score_bucket(60) == "60-69"
    assert scores.score_bucket(59.9) == "<60"


def test_delete_score(seeded):
    """删除已有成绩后查询为空。"""
    scores.record_score(seeded, "20230001", "高等数学", "2025-2026-1", 88)
    scores.delete_score(seeded, "20230001", "高等数学", "2025-2026-1")
    assert scores.query_scores(seeded, sno="20230001") == []


def test_delete_missing_score(seeded):
    """删除不存在的成绩应抛 NotFoundError。"""
    with pytest.raises(NotFoundError):
        scores.delete_score(seeded, "20230001", "高等数学", "2025-2026-1")
