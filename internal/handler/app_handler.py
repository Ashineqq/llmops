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
from pkg.stream.sse_stream import SSEStreamCache

from internal.schemas.app_schema import CompletionReq
from internal.service import AppService

_sse_cache = SSEStreamCache()


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
        """调用 DeepSeek 聊天补全 API（流式返回 SSE，支持断点续传）
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
                  stream_id:
                    type: string
                    description: 流会话 ID，客户端生成且重连时保持一致，用于断点续传
        responses:
          200:
            description: SSE 流式响应（每块 data 为 JSON 增量，带 id 事件，结束标记为 [DONE]）
            content:
              text/event-stream:
                schema:
                  type: string
        """
        body = request.get_json() or {}
        # 从表单数据中校验并获取查询内容
        form = CompletionReq(data=body)
        if not form.validate():
            return validate_error_json(form.errors)
        query = form.query.data
        stream_id = body.get("stream_id")
        last_event_id = request.headers.get("Last-Event-ID")

        def generate():
            try:
                if stream_id and last_event_id:
                    # 断点续传：从缓存续发 Last-Event-ID 之后的事件
                    try:
                        from_id = int(last_event_id)
                    except ValueError:
                        from_id = 0
                    for text in _sse_cache.stream_since(stream_id, from_id):
                        yield text
                    return
                # 首次生成（或无 stream_id 时退化为全量流式，不缓存）
                yield from self._generate_chain(query, stream_id)
            except Exception as e:
                payload = json.dumps({"error": str(e)}, ensure_ascii=False)
                if stream_id:
                    # 结束缓存流，避免续传端一直等待
                    _sse_cache.finish(stream_id)
                yield f"data: {payload}\n\n"

        resp = Response(generate(), mimetype="text/event-stream")
        resp.headers["Cache-Control"] = "no-cache"
        # 防止 Nginx 等反向代理缓冲流式响应
        resp.headers["X-Accel-Buffering"] = "no"
        return resp

    def _generate_chain(self, query: str, stream_id: str | None = None):
        """生成 DeepSeek 流式内容；传入 stream_id 时逐个事件写入缓存以支持断点续传。"""
        prompt_template = PromptTemplate.from_template("{query}")
        llm = ChatDeepSeek(
            model="deepseek-v4-flash",
        )
        parser = StrOutputParser()

        chain = prompt_template | llm | parser

        # invoke → stream，逐块以 SSE 格式 yield；有 stream_id 时每块带 id 事件
        for chunk in chain.stream({"query": query}):
            payload = json.dumps({"content": chunk}, ensure_ascii=False)
            if stream_id:
                event_id = _sse_cache.append(stream_id, chunk)
                yield f"id: {event_id}\ndata: {payload}\n\n"
            else:
                yield f"data: {payload}\n\n"
        if stream_id:
            _sse_cache.finish(stream_id)
        yield "data: [DONE]\n\n"
