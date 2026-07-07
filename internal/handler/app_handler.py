import os
from openai import OpenAI
from flask import request, jsonify
from internal.schemas.app_schema import AppCompletionReq


class AppHandler:
    """应用控制器"""

    def ping(self):
        return {"ping": "pong"}

    def completion(self):
        """调用 DeepSeek 聊天补全 API"""
        # 从表单数据中校验并获取查询内容
        form = AppCompletionReq(data=request.get_json())
        if not form.validate():
            return jsonify({"error": form.errors}), 400
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
            return jsonify({"completion": completion.choices[0].message.content})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
