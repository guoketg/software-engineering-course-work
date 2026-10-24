"""报表输出格式。

文件：report.py
功能：把查询结果渲染为等宽文本表格，把班级统计结果渲染为多行文本，
      供命令行界面直接打印。
主要函数：format_table、format_class_report。
"""

import unicodedata


def _text_width(text: str) -> int:
    """按终端显示宽度计算字符串长度，中文按 2 列计。"""
    width = 0
    for char in text:
        if unicodedata.east_asian_width(char) in ("W", "F"):
            width += 2
        else:
            width += 1
    return width


def _pad(text: str, width: int) -> str:
    """右侧补空格到指定显示宽度。"""
    return text + " " * (width - _text_width(text))


def _format_cell(value) -> str:
    """把单元格值转换为字符串，空值显示为空串。"""
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.1f}"
    return str(value)


def format_table(headers, rows) -> str:
    """渲染等宽文本表格。rows 为空时返回提示信息。"""
    header_cells = [str(header) for header in headers]
    if not rows:
        return "（无数据）"

    body = [[_format_cell(cell) for cell in row] for row in rows]
    widths = []
    for index, header in enumerate(header_cells):
        column_width = _text_width(header)
        for row in body:
            column_width = max(column_width, _text_width(row[index]))
        widths.append(column_width)

    header_line = " | ".join(
        _pad(header, widths[index]) for index, header in enumerate(header_cells)
    )
    separator = "-+-".join("-" * width for width in widths)
    lines = [header_line, separator]
    for row in body:
        lines.append(
            " | ".join(_pad(cell, widths[index]) for index, cell in enumerate(row))
        )
    return "\n".join(lines)


def format_class_report(report: dict) -> str:
    """渲染班级成绩统计报表为多行文本。"""
    distribution = report["distribution"]
    distribution_text = "  ".join(
        f"{bucket}: {count}" for bucket, count in distribution.items()
    )
    lines = [
        f"班级：{report['class_name']}  课程：{report['course']}  学期：{report['term']}",
        (
            f"记录条数：{report['count']}  平均分：{report['average']:.1f}"
            f"  最高分：{report['highest']:.1f}  最低分：{report['lowest']:.1f}"
        ),
        (
            f"及格人数：{report['pass_count']}"
            f"  及格率：{report['pass_rate']:.1f}%"
        ),
        f"分数段分布：{distribution_text}" if report["count"] else "分数段分布：（暂无成绩）",
    ]
    return "\n".join(lines)
