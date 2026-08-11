import threading
import time

from pkg.stream.sse_stream import SSEStreamCache


class TestSSEStreamCache:
    def setup_method(self):
        self.cache = SSEStreamCache(ttl=60)

    def test_append_returns_incrementing_id(self):
        assert self.cache.append("s1", "你好") == 1
        assert self.cache.append("s1", "世界") == 2
        assert self.cache.append("s1", "！") == 3

    def test_stream_since_full(self):
        self.cache.append("s1", "a")
        self.cache.finish("s1")

        events = "".join(self.cache.stream_since("s1", 0, timeout=1))
        assert "id: 1" in events
        assert 'data: {"content": "a"}' in events
        assert "data: [DONE]" in events

    def test_stream_since_resumes_from_last_id(self):
        self.cache.append("s1", "a")
        self.cache.append("s1", "b")
        self.cache.append("s1", "c")
        self.cache.finish("s1")

        events = "".join(self.cache.stream_since("s1", 1, timeout=1))
        assert "id: 1" not in events
        assert 'data: {"content": "b"}' in events
        assert 'data: {"content": "c"}' in events
        assert "data: [DONE]" in events

    def test_stream_since_waits_for_pending_stream(self):
        """流尚未生成完成时，续发端应等待新事件直到 [DONE]"""
        self.cache.append("s1", "a")

        collected: list[str] = []

        def consume():
            collected.extend(self.cache.stream_since("s1", 1, timeout=5))

        t = threading.Thread(target=consume)
        t.start()
        time.sleep(0.2)
        self.cache.append("s1", "b")
        self.cache.finish("s1")
        t.join(timeout=5)

        text = "".join(collected)
        assert 'data: {"content": "b"}' in text
        assert "data: [DONE]" in text

    def test_stream_since_timeout(self):
        self.cache.append("s1", "a")
        assert list(self.cache.stream_since("s1", 1, timeout=0.2)) == []

    def test_stream_since_unknown_stream(self):
        assert list(self.cache.stream_since("nope", 0, timeout=0.2)) == []

    def test_expired_stream_cleaned(self):
        cache = SSEStreamCache(ttl=0.01)
        cache.append("s1", "a")
        time.sleep(0.02)
        cache.append("s2", "b")
        assert list(cache.stream_since("s1", 0, timeout=0.1)) == []
