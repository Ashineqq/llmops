import os
import json
from unittest.mock import patch, MagicMock

import pytest
from openai import OpenAI


class TestAppHandler:
    """AppHandler 控制器测试"""

    @pytest.fixture(autouse=True)
    def setup_env(self):
        """每个测试前设置必要的环境变量"""
        os.environ["DEEPSEEK_API_KEY"] = "test-api-key"
        os.environ["DEEPSEEK_BASE_URL"] = "https://test.deepseek.com"
        yield
        # 清理环境变量
        os.environ.pop("DEEPSEEK_API_KEY", None)
        os.environ.pop("DEEPSEEK_BASE_URL", None)

    # ──────────────────────────────
    # completion — 成功场景
    # ──────────────────────────────

    @patch("internal.handler.app_handler.OpenAI")
    def test_completion_success(self, mock_openai, client):
        """正常请求应返回 completion 内容"""
        # 模拟 OpenAI 客户端的返回值
        mock_instance = MagicMock()
        mock_openai.return_value = mock_instance

        mock_choice = MagicMock()
        mock_choice.message.content = "你好，我是 DeepSeek AI 助手"
        mock_completion = MagicMock()
        mock_completion.choices = [mock_choice]
        mock_instance.chat.completions.create.return_value = mock_completion

        resp = client.post(
            "/v1/chat/completions",
            data=json.dumps({"query": "你好"}),
            content_type="application/json",
        )

        assert resp.status_code == 200
        data = resp.get_json()
        assert data["code"] == "success"
        assert data["data"]["completion"] == "你好，我是 DeepSeek AI 助手"

        # 验证 OpenAI 客户端构造参数
        mock_openai.assert_called_once_with(
            api_key="test-api-key",
            base_url="https://test.deepseek.com",
        )

        # 验证 API 调用参数
        mock_instance.chat.completions.create.assert_called_once_with(
            model="deepseek-v4-flash",
            messages=[
                {"role": "system", "content": "You are a helpful assistant"},
                {"role": "user", "content": "你好"},
            ],
        )

    # ──────────────────────────────
    # completion — 校验失败
    # ──────────────────────────────

    def test_completion_missing_query(self, client):
        """缺少 query 字段应返回 validation_error"""
        resp = client.post(
            "/v1/chat/completions",
            data=json.dumps({}),
            content_type="application/json",
        )

        assert resp.status_code == 200
        data = resp.get_json()
        assert data["code"] == "validation_error"
        assert data["message"] == "请输入查询内容"

    def test_completion_empty_query(self, client):
        """query 为空字符串应返回 validation_error"""
        resp = client.post(
            "/v1/chat/completions",
            data=json.dumps({"query": ""}),
            content_type="application/json",
        )

        assert resp.status_code == 200
        data = resp.get_json()
        assert data["code"] == "validation_error"

    @patch("internal.handler.app_handler.OpenAI")
    def test_completion_query_too_long(self, mock_openai, client):
        """query 超过 1024 字符应返回 validation_error"""
        resp = client.post(
            "/v1/chat/completions",
            data=json.dumps({"query": "a" * 1025}),
            content_type="application/json",
        )

        assert resp.status_code == 200
        data = resp.get_json()
        assert data["code"] == "validation_error"
        assert "1024" in data["message"] or "1024" in str(data["data"])

        # 验证 OpenAI 没有被调用
        mock_openai.assert_not_called()

    # ──────────────────────────────
    # completion — 异常场景
    # ──────────────────────────────

    @patch("internal.handler.app_handler.OpenAI")
    def test_completion_openai_api_error(self, mock_openai, client):
        """OpenAI API 调用失败应返回 fail_json"""
        mock_instance = MagicMock()
        mock_openai.return_value = mock_instance
        mock_instance.chat.completions.create.side_effect = Exception("Invalid API key")

        resp = client.post(
            "/v1/chat/completions",
            data=json.dumps({"query": "你好"}),
            content_type="application/json",
        )

        assert resp.status_code == 200
        data = resp.get_json()
        assert data["code"] == "fail"
        assert data["data"] == "Invalid API key"

    @patch("internal.handler.app_handler.OpenAI")
    def test_completion_default_base_url(self, mock_openai, client):
        """未设置 DEEPSEEK_BASE_URL 时应使用默认值"""
        os.environ.pop("DEEPSEEK_BASE_URL", None)

        mock_instance = MagicMock()
        mock_openai.return_value = mock_instance
        mock_choice = MagicMock()
        mock_choice.message.content = "OK"
        mock_completion = MagicMock()
        mock_completion.choices = [mock_choice]
        mock_instance.chat.completions.create.return_value = mock_completion

        client.post(
            "/v1/chat/completions",
            data=json.dumps({"query": "hi"}),
            content_type="application/json",
        )

        mock_openai.assert_called_once_with(
            api_key="test-api-key",
            base_url="https://api.deepseek.com",
        )
