from flask import Flask
import os

from internal.router import Router
from config import Config
from internal.exception import CustomException
from pkg.response import fail_json, json, Response
from pkg.sqlalchemy import SQLAlchemy
from internal.model import App


class Http(Flask):
    """http服务引擎"""

    def __init__(self, *args, db: SQLAlchemy, router: Router, config: Config, **kwargs):
        super().__init__(*args, **kwargs)
        # 捕获异常并处理
        self.register_error_handler(Exception, self._register_error_handler)
        # 应用配置
        self.config.from_object(config)
        # 初始化数据库
        db.init_app(self)
        with self.app_context():
            _ = App()
            db.create_all()
        # 注册应用路由
        router.register_router(self)

    def _register_error_handler(self, error: Exception):
        """注册异常处理函数"""
        # 1. 异常是自定义异常，是业务异常
        if isinstance(error, CustomException):
            return json(
                Response(
                    code=error.code,
                    message=error.message,
                    data=error.data if error.data is not None else {},
                )
            )

        # 2. 异常是程序、数据库等非自定义异常
        if os.getenv("FLASK_ENV") == "development":
            raise error
        else:
            return fail_json(str(error))
