from flask import Blueprint, Flask
from injector import inject

from internal.handler import AppHandler


@inject
class Router:
    """路由"""

    app_handler: AppHandler

    def __init__(self, app_handler: AppHandler):
        self.app_handler = app_handler

    def register_router(self, app: Flask):

        # 1.创建蓝图
        bp = Blueprint("llmops", __name__, url_prefix="")

        # 2.将url与对应的控制器方法做绑定
        bp.add_url_rule("/ping", view_func=self.app_handler.ping)
        bp.add_url_rule(
            "/v1/chat/completions",
            view_func=self.app_handler.completion,
            methods=["POST"],
        )

        # 3.在应用上去注册蓝图
        app.register_blueprint(bp)
