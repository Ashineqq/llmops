import os
from openai import OpenAI
from flask import request
from internal.schemas.app_schema import CompletionReq
from pkg.response import (
    success_json,
    fail_json,
    validate_error_json,
    success_message,
    not_found_message,
)
from internal.service import AppService
from dataclasses import dataclass
from injector import inject
import uuid


@inject
@dataclass
class AppHandler:
    """应用控制器"""

    app_service: AppService

    def create_app(self):
        """创建新的app应用"""
        app = self.app_service.create_app()
        return success_message(f"应用创建成功，应用ID为：{app.id}")

    def get_app(self, id: uuid.UUID):
        """获取应用"""
        app = self.app_service.get_app(id)
        return success_message(
            f"应用ID为{id}的应用信息：名称：{app.name}，账号ID：{app.account_id}，描述：{app.description}"
        )

    def update_app(self, id: uuid.UUID):
        """更新应用"""
        app = self.app_service.update_app(id)

        return success_message(f"应用ID为{id}的应用已更新，新名称：{app.name}")

    def delete_app(self, id: uuid.UUID):
        """删除应用"""
        app = self.app_service.delete_app(id)
        return success_message(f"应用ID为{app.id}的应用已删除")

    def completion(self):
        """调用 DeepSeek 聊天补全 API"""
        # 从表单数据中校验并获取查询内容
        form = CompletionReq(data=request.get_json())
        if not form.validate():
            return validate_error_json(form.errors)
        query = form.query.data

        # 从环境变量中获取 DeepSeek API 密钥和基础 URL，并创建 OpenAI 客户端
        api_key = os.getenv("DEEPSEEK_API_KEY")
        base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        client = OpenAI(api_key=api_key, base_url=base_url)

        try:
            completion = client.chat.completions.create(
                model="deepseek-v4-flash",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant"},
                    {"role": "user", "content": query},
                ],
            )

            return success_json({"completion": completion.choices[0].message.content})
        except Exception as e:
            return fail_json(str(e))
