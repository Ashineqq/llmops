import os

from config import Config
from flasgger import Swagger
from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate
from pkg.response import Response, fail_json, json
from pkg.sqlalchemy import SQLAlchemy

from internal.exception import CustomException
from internal.model import App
from internal.router import Router


class Http(Flask):
    """http服务引擎"""

    def __init__(
        self,
        *args,
        migrate: Migrate,
        db: SQLAlchemy,
        router: Router,
        config: Config,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        # 捕获异常并处理
        self.register_error_handler(Exception, self._register_error_handler)
        # 应用配置
        self.config.from_object(config)
        # 初始化数据库
        db.init_app(self)
        migrate.init_app(self, db, directory="internal/migration")
        with self.app_context():
            _ = App()
            db.create_all()
        # 添加跨域处理
        CORS(
            self,
            resources={
                r"/*": {
                    "origins": "*",
                    "supports_credentials": True,
                }
            },
        )
        # 注册应用路由
        router.register_router(self)
        # 注册 Swagger UI + OpenAPI spec（/apidocs/ 查看文档，/apispec_1.json 输出 spec）
        # config 里显式声明 openapi 版本：否则 flasgger 默认写入 swagger: "2.0"，
        # 与 template 的 openapi: "3.0.0" 共存会导致 Swagger UI 渲染报错
        self.swagger = Swagger(
            self,
            config={"openapi": "3.0.0"},
            merge=True,
            template={
                "openapi": "3.0.0",
                "info": {
                    "title": "LLM Ops API",
                    "description": "LLM 运维平台接口文档",
                    "version": "0.1.0",
                },
            },
        )

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
