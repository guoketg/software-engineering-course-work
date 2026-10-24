"""业务异常定义。

文件：errors.py
功能：统一各模块抛出的业务异常类型，便于命令行界面集中捕获并提示。
"""


class AppError(Exception):
    """业务异常基类。"""


class ValidationError(AppError):
    """输入数据不符合校验规则。"""


class NotFoundError(AppError):
    """目标数据不存在。"""


class DuplicateError(AppError):
    """违反唯一性约束。"""


class AuthError(AppError):
    """身份认证失败。"""


class AccessDeniedError(AppError):
    """角色权限不足。"""


class BackupError(AppError):
    """备份文件损坏或恢复过程失败。"""
