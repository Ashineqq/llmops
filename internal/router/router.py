from flask import Blueprint, Flask
from injector import inject
from dataclasses import dataclass
from internal.handler import AppHandler


@inject
@dataclass
class Router:
    """路由"""

    app_handler: AppHandler

    def register_router(self, app: Flask):

        # 1.创建蓝图
        bp = Blueprint("llmops", __name__, url_prefix="")

        # 2.将url与对应的控制器方法做绑定
        bp.add_url_rule(
            "/v1/chat/completions",
            methods=["POST"],
            view_func=self.app_handler.completion,
        )
        bp.add_url_rule("/app", methods=["POST"], view_func=self.app_handler.create_app)
        bp.add_url_rule("/app/<uuid:id>", view_func=self.app_handler.get_app)
        bp.add_url_rule("/app/<uuid:id>", methods=["POST"], view_func=self.app_handler.update_app)
        bp.add_url_rule("/app/<uuid:id>/delete", methods=["POST"], view_func=self.app_handler.delete_app)

        # 3.在应用上去注册蓝图
        app.register_blueprint(bp)
