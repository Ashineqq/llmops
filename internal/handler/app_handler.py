import json
import uuid
from dataclasses import dataclass

from flask import Response, request
from injector import inject
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_deepseek import ChatDeepSeek
from pkg.response import (
    success_message,
    validate_error_json,
)

from internal.schemas.app_schema import CompletionReq
from internal.service import AppService


@inject
@dataclass
class AppHandler:
    """应用控制器"""

    app_service: AppService

    def create_app(self):
        """创建新的 app 应用
        ---
        tags: [app]
        operationId: createApp
        responses:
          200:
            description: 创建成功，返回应用 ID 信息
            content:
              application/json:
                schema:
                  type: object
        """
        app = self.app_service.create_app()
        return success_message(f"应用创建成功，应用ID为：{app.id}")

    def get_app(self, id: uuid.UUID):
        """获取应用
        ---
        tags: [app]
        operationId: getApp
        parameters:
          - name: id
            in: path
            required: true
            description: 应用 ID
            schema:
              type: string
              format: uuid
        responses:
          200:
            description: 应用信息
            content:
              application/json:
                schema:
                  type: object
        """
        app = self.app_service.get_app(id)
        return success_message(
            f"应用ID为{id}的应用信息：名称：{app.name}，账号ID：{app.account_id}，描述：{app.description}"
        )

    def update_app(self, id: uuid.UUID):
        """更新应用
        ---
        tags: [app]
        operationId: updateApp
        parameters:
          - name: id
            in: path
            required: true
            description: 应用 ID
            schema:
              type: string
              format: uuid
        responses:
          200:
            description: 更新成功
            content:
              application/json:
                schema:
                  type: object
        """
        app = self.app_service.update_app(id)
        return success_message(f"应用ID为{id}的应用已更新，新名称：{app.name}")

    def delete_app(self, id: uuid.UUID):
        """删除应用
        ---
        tags: [app]
        operationId: deleteApp
        parameters:
          - name: id
            in: path
            required: true
            description: 应用 ID
            schema:
              type: string
              format: uuid
        responses:
          200:
            description: 删除成功
            content:
              application/json:
                schema:
                  type: object
        """
        app = self.app_service.delete_app(id)
        return success_message(f"应用ID为{app.id}的应用已删除")

    def completion(self):
        """调用 DeepSeek 聊天补全 API（流式返回 SSE）
        ---
        tags: [chat]
        operationId: chatCompletion
        requestBody:
          required: true
          content:
            application/json:
              schema:
                type: object
                required: [query]
                properties:
                  query:
                    type: string
                    description: 用户输入
        responses:
          200:
            description: SSE 流式响应（每块 data 为 JSON 增量，结束标记为 [DONE]）
            content:
              text/event-stream:
                schema:
                  type: string
        """
        # 从表单数据中校验并获取查询内容
        form = CompletionReq(data=request.get_json())
        if not form.validate():
            return validate_error_json(form.errors)
        query = form.query.data

        def generate():
            try:
                # 实例化与调用都放入生成器内，任何异常都会被捕获为 SSE error 分块
                prompt_template = PromptTemplate.from_template("{query}")
                llm = ChatDeepSeek(
                    model="deepseek-v4-flash",
                )
                parser = StrOutputParser()

                chain = prompt_template | llm | parser

                # invoke → stream，逐块以 SSE 格式 yield
                for chunk in chain.stream({"query": query}):
                    payload = json.dumps({"content": chunk}, ensure_ascii=False)
                    yield f"data: {payload}\n\n"
                yield "data: [DONE]\n\n"
            except Exception as e:
                payload = json.dumps({"error": str(e)}, ensure_ascii=False)
                yield f"data: {payload}\n\n"

        resp = Response(generate(), mimetype="text/event-stream")
        resp.headers["Cache-Control"] = "no-cache"
        # 防止 Nginx 等反向代理缓冲流式响应
        resp.headers["X-Accel-Buffering"] = "no"
        return resp
