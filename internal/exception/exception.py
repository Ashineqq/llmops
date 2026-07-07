from pkg.response import HttpCode
from dataclasses import field
from typing import Any


class CustomException(Exception):
    """自定义异常基类"""
    code: HttpCode = HttpCode.FAIL
    message: str = ""
    data: Any = field(default_factory=dict)

    def __init__(self, message: str = "", data: Any = None):
        super().__init__()
        self.message = message
        self.data = data

class FailException(CustomException):
    """失败异常"""
    pass

class ValidateException(CustomException):
    """校验异常"""
    code: HttpCode = HttpCode.VALIDATION_ERROR

class NotFoundException(CustomException):
    """未找到异常"""
    code: HttpCode = HttpCode.NOT_FOUND

class UnauthorizedException(CustomException):
    """未授权异常"""
    code: HttpCode = HttpCode.UNAUTHORIZED

class ForbiddenException(CustomException):
    """禁止异常"""
    code: HttpCode = HttpCode.FORBIDDEN
