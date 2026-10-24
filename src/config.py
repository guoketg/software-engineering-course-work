"""全局配置常量。

文件：config.py
功能：集中定义数据目录、数据库路径、字段长度与分数阈值等常量，
      供各业务模块统一引用，避免在代码中出现魔法数字。
"""

from pathlib import Path

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent

# 数据目录与数据库文件
DATA_DIR = BASE_DIR / "data"
BACKUP_DIR = DATA_DIR / "backups"
DB_PATH = DATA_DIR / "school.db"

# 角色与性别取值范围
VALID_ROLES = ("student", "teacher", "admin")
VALID_GENDERS = ("男", "女")

# 学号与口令长度限制
SNO_MIN_LEN = 6
SNO_MAX_LEN = 20
PASSWORD_MIN_LEN = 6
PASSWORD_MAX_LEN = 64

# 成绩取值范围与及格线
MIN_SCORE = 0.0
MAX_SCORE = 100.0
PASS_SCORE = 60.0

# 成绩分布统计的分数段
DISTRIBUTION_BUCKETS = ("90-100", "80-89", "70-79", "60-69", "<60")
