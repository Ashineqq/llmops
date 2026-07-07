# LLMOps API — Agent 备忘录

## 项目概述

基于 Flask + injector 的 LLM Ops 后端服务，提供 DeepSeek API 的代理调用接口。

- **仓库**: `https://github.com/Ashineqq/llmops.git`（分支 `main`）
- **入口文件**: `app/http/app.py`
- **框架**: Flask（自定义 `Http` 类继承 `Flask`）
- **DI 容器**: `injector`
- **LLM SDK**: `openai`（OpenAI SDK 风格调用 DeepSeek API）
- **端口**: `5000`

## 项目结构

```
llmops-api/
├── app/http/app.py              # 应用入口，加载 .env，创建 Flask app
├── internal/
│   ├── handler/app_handler.py   # 控制器（ping / completion）
│   ├── router/router.py         # 路由注册（Blueprint）
│   └── server/http.py           # Flask 封装
├── .env                         # 环境变量（API Key、Base URL）
├── requirements.txt
└── agent.md
```

## 环境与依赖

### 激活虚拟环境

```bash
source .venv/bin/activate
```

所有 Python 操作（pip install、运行、调试）都必须在虚拟环境中执行。

### 安装依赖

```bash
pip install -r requirements.txt
```

### 核心依赖

| 包名 | 用途 |
|---|---|
| `flask` | Web 框架 |
| `injector` | 依赖注入 |
| `python-dotenv` | 加载 `.env` 文件 |
| `openai` | OpenAI SDK（兼容模式调用 DeepSeek） |

## 运行方式

```bash
python app/http/app.py
```

## 环境变量（.env）

```env
DEEPSEEK_API_KEY=sk-xxxx
DEEPSEEK_BASE_URL=https://api.deepseek.com
```

`load_dotenv()` 在 `app/http/app.py` 入口处调用，全局生效。

## 已踩坑点

### 1. `.venv` 虚拟环境
沙箱中的 Python 操作必须先激活 `.venv`，否则依赖会装到系统级目录，导致 import 失败或权限错误。

### 2. `remote origin already exists`
添加远程仓库时如果 `origin` 已存在，需用 `git remote set-url origin <url>` 而非 `git remote add`。

### 3. `load_dotenv()` 位置
`load_dotenv()` 应放在应用入口文件（`app.py`），而不是在 handler 中重复调用。避免多次加载，确保全局统一读取。

### 4. pipreqs 扫描范围
`pipreqs` 在该环境中会扫描系统 Python 的 site-packages，生成大量无关依赖。更好的做法是直接根据 `import` 语句手动维护 `requirements.txt`。

### 5. macOS 外部托管 Python 环境
macOS 系统 Python 是 `externally-managed-environment`，直接 `pip install` 会报错。解决方式：
  - 使用虚拟环境 `.venv`（推荐）
  - 或 `pip3 install --user --break-system-packages`
