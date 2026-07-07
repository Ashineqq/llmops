from flask import Flask

from internal.router import Router
from config import Config
from injector import Injector


class Http(Flask):
    """http服务引擎"""

    def __init__(self, *args, router: Injector.get(Router), config: Config, **kwargs):
        super().__init__(*args, **kwargs)
        # 注册应用路由
        router.register_router(self)
        # 应用配置
        self.config.from_object(config)
