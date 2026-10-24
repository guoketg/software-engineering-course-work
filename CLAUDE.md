# CLAUDE.md

本文件是本项目的约束入口。每轮开始工作前先读本文件，再读 `docs/progress.md`。

## 项目目标

学生成绩管理系统，面向学生、教师、管理员三类参与者：

- 学生：提交成绩查询请求，获取个人成绩信息。
- 教师：录入成绩、查询成绩、获取班级成绩报表。
- 管理员：负责系统后台维护，包含四大处理模块。

四大模块：

- P1 学生信息管理：操作学生基本信息表，完成学生信息增、删、改、查。
- P2 成绩业务管理：读写成绩数据表，完成成绩录入、查询，生成成绩统计报表。
- P3 用户权限管理：维护系统用户表，管控不同角色账号与访问权限。
- P4 数据集备份与恢复：读写系统备份文件，实现数据库备份与故障后恢复。

## 技术栈与版本

- Python 3.12.10
- 虚拟环境：项目根目录 `.venv/`（默认，必须使用）
- 数据库：SQLite 3（Python 标准库 `sqlite3`），库文件 `data/school.db`
- 界面：命令行交互界面（`argparse` + 菜单），入口 `python -m src.main`
- 测试：pytest 9.1.1，用例数上限 50

## 环境与命令

在项目根目录执行（PowerShell）：

```powershell
# 首次创建虚拟环境
python -m venv .venv

# 安装依赖
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

# 运行测试
.\.venv\Scripts\python.exe -m pytest
```

规则：

- 所有 Python 命令显式使用 `.\.venv\Scripts\python.exe`，不依赖 `activate` 在命令间保持生效。
- 禁止全局 `pip install`；依赖只装进 `.venv`。
- 依赖变更后执行 `.\.venv\Scripts\python.exe -m pip freeze > requirements.txt`。

## 目录结构

- `src/`：系统实现代码。`cli.py`、`main.py` 为界面层；`students.py`（P1）、`scores.py`（P2）、`auth.py` 与 `security.py`（P3）、`backup.py`（P4）为业务层；`db.py` 为数据层；`report.py`、`errors.py`、`config.py`、`seed.py` 为支撑模块。
- `tests/`：pytest 测试用例，含输入校验、四大模块单元测试与命令行集成/功能测试。
- `data/`：运行期数据库与备份文件，不提交。
- `docs/`：实验资料与项目文档。PDF/Word 为只读原始资料，同名 `.md` 为供 AI 阅读的转换副本。
- `docs/progress.md`：实现进度与决策记录。
- `docs/实验三_系统实现报告.md`：详细设计、模块算法与数据库物理设计。
- `docs/实验四_系统测试报告.md`：测试计划、测试用例与测试结论。
- `.venv/`：项目级虚拟环境，不提交。
- `.trae/skills/`：项目级 skill，包含 `python-project-conventions`、`pdf-to-markdown`、`word-to-markdown`。

## 文档与进度规则

- `docs/` 下的 PDF、Word 原始资料只读，不修改、不覆盖、不删除。
- 转换出的 `.md` 是派生副本，内容以原始文件为准。
- 每次里程碑完成后在 `docs/progress.md` 追加带日期的记录，只追加不回写历史。
- 新增文档后在本文档「目录结构」中登记。

## 开发约定

- 编码前先确认当前任务与约束来自 `CLAUDE.md` 和 `docs/progress.md`。
- 变更完成后运行约定的验证命令，再更新进度文档。
- 命名、分支、提交规范待项目代码落地后补充。

## 禁止事项

- 禁止使用全局 Python 环境安装依赖。
- 禁止修改或删除 `docs/` 下的原始资料。
- 禁止未经运行验证就声称任务完成。
- 禁用 Trae 可视化能力：不调用 `PureShowWidget`，不加载 `dynamic-ui` skill，不生成内联图表或交互组件，说明使用文字、Markdown 代码块或项目内文件。
- 禁用专家或顾问调用：不调用 `AdvisorTool` 及任何「专家评审 / 顾问」类能力，遇到阻塞时自行分析或直接向用户提问。

## 关键决策记录

- 2026-10-23：确立项目级虚拟环境 `.venv` 为默认运行环境。
- 2026-10-23：创建项目规范 skill `python-project-conventions`。
- 2026-10-23：将 `docs/` 下实验资料转换为 Markdown 供 AI 阅读，原始文件保持只读。
- 2026-10-23：禁用 Trae 可视化能力（`PureShowWidget` / `dynamic-ui`）。
- 2026-10-23：禁用专家或顾问调用（`AdvisorTool`）。
- 2026-10-23：技术栈定为 Python 3.12 + SQLite 3 + 命令行界面，不引入 Web 框架。
- 2026-10-23：完成实验三系统实现，P1~P4 模块落在 `src/`，入口 `python -m src.main`。
- 2026-10-23：完成实验四系统测试，50 项 pytest 用例全部通过，报告见 `docs/实验四_系统测试报告.md`。
