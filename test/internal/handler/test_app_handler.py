import json
import os
from unittest.mock import patch

import pytest


def _parse_sse(resp) -> list[str]:
    """从 SSE 响应中提取所有 data: 行的值"""
    return [
        line[len("data:") :].strip()
        for line in resp.text.splitlines()
        if line.startswith("data:")
    ]


class TestAppHandler:
    """AppHandler 控制器测试"""

    @pytest.fixture(autouse=True)
    def setup_env(self):
        """每个测试前设置必要的环境变量并清理断点续传缓存"""
        os.environ["DEEPSEEK_API_KEY"] = "test-api-key"
        os.environ["DEEPSEEK_BASE_URL"] = "https://test.deepseek.com"
        from internal.handler import app_handler as h

        h._sse_cache.clear()
        yield
        os.environ.pop("DEEPSEEK_API_KEY", None)
        os.environ.pop("DEEPSEEK_BASE_URL", None)

    @pytest.fixture
    def mock_chain(self):
        """mock langchain 组件，返回 chain mock（chain.stream 可控制）"""
        with (
            patch("internal.handler.app_handler.ChatDeepSeek") as mock_llm,
            patch("internal.handler.app_handler.PromptTemplate") as mock_prompt,
            patch("internal.handler.app_handler.StrOutputParser") as mock_parser,
        ):
            chain = (
                mock_prompt.from_template.return_value
                | mock_llm.return_value
                | mock_parser.return_value
            )
            yield chain, mock_llm

    # ──────────────────────────────
    # completion — 成功场景
    # ──────────────────────────────

    def test_completion_success(self, mock_chain, client):
        """正常请求应以 SSE 流式返回完整内容"""
        chain, _ = mock_chain
        chain.stream.return_value = iter(["你好", "，我是", "AI"])

        resp = client.post(
            "/api/v1/chat/completions",
            data=json.dumps({"query": "你好"}),
            content_type="application/json",
        )

        assert resp.status_code == 200
        assert resp.content_type.startswith("text/event-stream")
        data_lines = _parse_sse(resp)
        contents = [json.loads(line)["content"] for line in data_lines[:-1]]
        assert "".join(contents) == "你好，我是AI"
        assert data_lines[-1] == "[DONE]"

    def test_completion_default_model(self, mock_chain, client):
        """未显式指定时 ChatDeepSeek 使用默认模型"""
        chain, mock_llm = mock_chain
        chain.stream.return_value = iter(["OK"])

        client.post(
            "/api/v1/chat/completions",
            data=json.dumps({"query": "hi"}),
            content_type="application/json",
        )

        mock_llm.assert_called_once_with(model="deepseek-v4-flash")

    # ──────────────────────────────
    # completion — 校验失败
    # ──────────────────────────────

    def test_completion_missing_query(self, client):
        """缺少 query 字段应返回 validation_error"""
        resp = client.post(
            "/api/v1/chat/completions",
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
            "/api/v1/chat/completions",
            data=json.dumps({"query": ""}),
            content_type="application/json",
        )

        assert resp.status_code == 200
        data = resp.get_json()
        assert data["code"] == "validation_error"

    def test_completion_query_too_long(self, client):
        """query 超过 1024 字符应返回 validation_error"""
        resp = client.post(
            "/api/v1/chat/completions",
            data=json.dumps({"query": "a" * 1025}),
            content_type="application/json",
        )

        assert resp.status_code == 200
        data = resp.get_json()
        assert data["code"] == "validation_error"
        assert "1024" in data["message"] or "1024" in str(data["data"])

    # ──────────────────────────────
    # completion — 异常场景
    # ──────────────────────────────

    def test_completion_stream_error(self, mock_chain, client):
        """chain 抛异常应返回 SSE error 分块"""
        chain, _ = mock_chain
        chain.stream.side_effect = Exception("Invalid API key")

        resp = client.post(
            "/api/v1/chat/completions",
            data=json.dumps({"query": "你好"}),
            content_type="application/json",
        )

        assert resp.status_code == 200
        data_lines = _parse_sse(resp)
        payload = json.loads(data_lines[0])
        assert "error" in payload
        assert payload["error"] == "Invalid API key"

    # ──────────────────────────────
    # completion — 断点续传
    # ──────────────────────────────

    def test_completion_events_carry_id(self, mock_chain, client):
        """带 stream_id 时每个事件应携带自增 id"""
        chain, _ = mock_chain
        chain.stream.return_value = iter(["你好", "世界"])

        resp = client.post(
            "/api/v1/chat/completions",
            data=json.dumps({"query": "hi", "stream_id": "sid-1"}),
            content_type="application/json",
        )

        assert resp.status_code == 200
        assert "id: 1" in resp.text
        assert "id: 2" in resp.text

    def test_completion_resume_from_last_event_id(self, mock_chain, client):
        """断线重连（带 Last-Event-ID）应只续发后续内容"""
        chain, _ = mock_chain
        chain.stream.return_value = iter(["你好", "世界"])

        resp1 = client.post(
            "/api/v1/chat/completions",
            data=json.dumps({"query": "hi", "stream_id": "sid-1"}),
            content_type="application/json",
        )
        data1 = _parse_sse(resp1)
        assert "".join(json.loads(line)["content"] for line in data1[:-1]) == "你好世界"

        # 模拟客户端已收到 id: 1 后断线重连
        resp2 = client.post(
            "/api/v1/chat/completions",
            data=json.dumps({"query": "hi", "stream_id": "sid-1"}),
            headers={"Last-Event-ID": "1"},
            content_type="application/json",
        )
        data2 = _parse_sse(resp2)
        contents2 = [json.loads(line)["content"] for line in data2[:-1]]
        assert "".join(contents2) == "世界"
        assert data2[-1] == "[DONE]"
