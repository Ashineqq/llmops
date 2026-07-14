import os
import sys

# 将项目根目录加入 sys.path，确保 internal/ 等顶层包可被导入
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from dotenv import load_dotenv
from injector import Injector
from internal.router import Router  
from internal.server import Http
from config import Config
from app.http.module import ExtensionModule
from flask_sqlalchemy import SQLAlchemy


load_dotenv()

injector = Injector([ExtensionModule])

app = Http(
    __name__, db=injector.get(SQLAlchemy), router=injector.get(Router), config=Config()
)

if __name__ == "__main__":
    app.run(debug=True)
