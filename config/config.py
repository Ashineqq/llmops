import os
from .default_config import DEFAULT_CONFIG
from typing import Any


def _get_env(key: str) -> Any:
    return os.getenv(key, DEFAULT_CONFIG.get(key))


def _get_bool_env(key: str) -> bool:
    value = _get_env(key)
    return value.lower() == "true"
 

def _get_int_env(key: str) -> int:
    return int(_get_env(key))


class Config:
    """应用配置类"""

    def __init__(self):
        # 是否开启 CSRF 保护
        self.WTF_CSRF_ENABLED = _get_bool_env("WTF_CSRF_ENABLED")
 
        # 数据库配置
        self.SQLALCHEMY_DATABASE_URI = _get_env("SQLALCHEMY_DATABASE_URI")
        self.SQLALCHEMY_ENGINE_OPTIONS = {
            "pool_size": _get_int_env("SQLALCHEMY_POOL_SIZE"),
            "pool_recycle": _get_int_env("SQLALCHEMY_POOL_RECYCLE"),
        }
        self.SQLALCHEMY_ECHO = _get_bool_env("SQLALCHEMY_ECHO")
