"""口令散列工具。

文件：security.py
功能：使用 PBKDF2-HMAC-SHA256 加盐散列保存口令，数据库中不出现明文。
      主要函数：make_salt、hash_password、verify_password。
"""

import hashlib
import hmac
import secrets

# 迭代次数与盐长度
ITERATIONS = 100_000
SALT_BYTES = 16


def make_salt() -> str:
    """生成随机盐，返回十六进制字符串。"""
    return secrets.token_hex(SALT_BYTES)


def hash_password(password: str, salt: str) -> str:
    """按给定盐计算口令散列，返回十六进制字符串。"""
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt),
        ITERATIONS,
    )
    return digest.hex()


def verify_password(password: str, salt: str, expected_hash: str) -> bool:
    """校验口令是否与保存的散列一致。"""
    actual_hash = hash_password(password, salt)
    return hmac.compare_digest(actual_hash, expected_hash)
