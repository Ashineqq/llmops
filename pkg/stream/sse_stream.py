import json
import threading
import time


class _StreamData:
    """单个流的缓存数据"""

    def __init__(self, expire_at: float):
        self.events: list[tuple[int, str]] = []  # [(事件 id, 完整 SSE 事件文本)]
        self.next_id = 1
        self.done = False
        self.expire_at = expire_at

    def refresh(self, expire_at: float) -> None:
        self.expire_at = expire_at


class SSEStreamCache:
    """线程安全的 SSE 断点续传缓存（进程内内存实现）。

    以 stream_id 为键，缓存每个事件的完整 SSE 文本（事件 id 从 1 自增）。
    断线重连时通过 stream_since 从 Last-Event-ID 之后续发；若流尚未生成完成，
    续发端会等待新事件，直到收到 [DONE] 或超时。
    """

    def __init__(self, ttl: int = 600):
        self._ttl = ttl
        self._streams: dict[str, _StreamData] = {}
        self._cond = threading.Condition()

    def _expire_at(self) -> float:
        return time.time() + self._ttl

    def _cleanup(self) -> None:
        now = time.time()
        for sid in [sid for sid, d in self._streams.items() if d.expire_at <= now]:
            del self._streams[sid]

    def append(self, stream_id: str, content: str) -> int:
        """追加一个内容块，返回其事件 id。"""
        with self._cond:
            self._cleanup()
            data = self._streams.get(stream_id)
            if data is None:
                data = _StreamData(self._expire_at())
                self._streams[stream_id] = data
            data.refresh(self._expire_at())
            event_id = data.next_id
            payload = json.dumps({"content": content}, ensure_ascii=False)
            data.events.append((event_id, f"id: {event_id}\ndata: {payload}\n\n"))
            data.next_id += 1
            self._cond.notify_all()
            return event_id

    def finish(self, stream_id: str) -> None:
        """标记流结束，追加 [DONE] 事件。"""
        with self._cond:
            data = self._streams.get(stream_id)
            if data is None:
                return
            event_id = data.next_id
            data.events.append((event_id, f"id: {event_id}\ndata: [DONE]\n\n"))
            data.next_id += 1
            data.done = True
            self._cond.notify_all()

    def stream_since(self, stream_id: str, last_id: int, timeout: float = 60.0):
        """返回生成器：续发 id > last_id 的事件。

        若流尚未完成，会等待新事件；收到 [DONE] 或超过 timeout 后结束。
        """

        def gen():
            nonlocal last_id
            deadline = time.time() + timeout
            while True:
                with self._cond:
                    data = self._streams.get(stream_id)
                    if data is None:
                        return
                    to_send = [text for eid, text in data.events if eid > last_id]
                    if to_send:
                        last_id = data.events[-1][0]
                    done = data.done
                for text in to_send:
                    yield text
                if done:
                    return
                if time.time() >= deadline:
                    return
                with self._cond:
                    self._cond.wait(0.5)

        return gen()

    def clear(self) -> None:
        """清空缓存（测试用）。"""
        with self._cond:
            self._streams.clear()
