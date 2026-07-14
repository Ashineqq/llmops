from flask_sqlalchemy import SQLAlchemy
from injector import inject
from dataclasses import dataclass
from internal.model import App
import uuid

@inject
@dataclass
class AppService:
    """应用服务逻辑"""
    db: SQLAlchemy

    def create_app(self)-> App:
        """创建应用"""
        app = App(name="实体机器人",account_id=uuid.uuid4(),description="这是一个实体机器人应用")
        """将ORM实体类添加到会话中"""
        self.db.session.add(app)
        """提交session会话"""
        self.db.session.commit()
        return app
    
    def get_app(self,id: uuid.UUID)-> App:
        """获取应用"""
        app = self.db.session.query(App).get(id)
        return app
    
    def update_app(self, id: uuid.UUID)-> App:
        """更新应用"""
        app = self.get_app(id)
        app.name = "实体机器人-更新"
        self.db.session.commit()
        return app
    
    def delete_app(self, id: uuid.UUID)-> None:
        """删除应用"""
        app = self.get_app(id)
        self.db.session.delete(app)
        self.db.session.commit()
        return app