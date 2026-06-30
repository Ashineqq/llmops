import os
import sys
from injector import Injector

# 将项目根目录加入 sys.path，确保 internal/ 等顶层包可被导入
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from internal.router import Router
from internal.server import Http

injector = Injector()

app = Http(__name__, router=injector.get(Router))

if __name__ == "__main__":
    app.run(debug=True)
