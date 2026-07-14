from injector import Module, Binder
from internal.extension.database_extension import db
from pkg.sqlalchemy import SQLAlchemy
from internal.extension.migrate_extension import migrate
from flask_migrate import Migrate

class ExtensionModule(Module):
    """扩展模块"""

    def configure(self, binder: Binder) -> None:
        # 绑定数据库扩展
        binder.bind(SQLAlchemy, to=db)
        binder.bind(Migrate, to=migrate)
