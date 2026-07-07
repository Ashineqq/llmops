from .http_code import HttpCode
from typing import Any
from dataclasses import dataclass, field
from flask import jsonify


@dataclass
class Response:
    """响应基类"""

    code: HttpCode = HttpCode.SUCCESS
    message: str = ""
    data: Any = field(default_factory=dict)


def json(data: Any = None):
    """将数据转换为 JSON 字符串"""
    return jsonify(data), 200


def success_json(data: Any = None):
    """将成功响应转换为 JSON 字符串"""
    return json(Response(code=HttpCode.SUCCESS, message="", data=data))


def fail_json(data: str = ""):
    """将失败响应转换为 JSON 字符串"""
    return json(Response(code=HttpCode.FAIL, message="", data=data))


def validate_error_json(errors: dict = None):
    """将验证响应转换为 JSON 字符串"""
    first_key = next(iter(errors))
    if first_key is not None:
        msg = errors.get(first_key)[0]
    else:
        msg = ""
    return json(Response(code=HttpCode.VALIDATION_ERROR, message=msg, data=errors))


def message(code: HttpCode, msg: str = ""):
    """将消息转换为 JSON 字符串"""
    return json(Response(code=code, message=msg, data={}))


def success_message(msg: str = ""):
    """将成功消息转换为 JSON 字符串"""
    return message(HttpCode.SUCCESS, msg)


def fail_message(msg: str = ""):
    """将失败消息转换为 JSON 字符串"""
    return message(HttpCode.FAIL, msg)


def not_found_message(msg: str = ""):
    """将未找到消息转换为 JSON 字符串"""
    return message(HttpCode.NOT_FOUND, msg)


def unauthorized_message(msg: str = ""):
    """将未授权消息转换为 JSON 字符串"""
    return message(HttpCode.UNAUTHORIZED, msg)


def forbidden_message(msg: str = ""):
    """将禁止消息转换为 JSON 字符串"""
    return message(HttpCode.FORBIDDEN, msg)
