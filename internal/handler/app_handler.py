from openai import OpenAI
from flask import request
from internal.schemas.app_schema import CompletionReq
from pkg.response import (
    success_json,
    validate_error_json,
    success_message,
)
from internal.service import AppService
from dataclasses import dataclass
from injector import inject
import uuid
from langchain_core.prompts import PromptTemplate
from langchain_deepseek import ChatDeepSeek
from langchain_core.output_parsers import StrOutputParser


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

        prompt_template = PromptTemplate.from_template("{query}")
        llm = ChatDeepSeek(
            model="deepseek-v4-flash",
        )
        parser = StrOutputParser()

        chain = prompt_template | llm | parser
        content = chain.invoke({"query": query})

        return success_json({"content": content})
