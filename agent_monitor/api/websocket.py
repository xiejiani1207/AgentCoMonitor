"""WebSocket 连接管理器——向所有已连接客户端广播事件。"""

import json
import logging
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WebSocketManager:
    """管理 WebSocket 连接，支持广播推送。

    用法:
        ws_manager = WebSocketManager()
        collector = TraceCollector(ws_notifier=ws_manager.broadcast_event)
    """

    def __init__(self):
        self._connections: list[WebSocket] = []

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self._connections.append(ws)
        logger.info("websocket connected (total=%d)", len(self._connections))

    def disconnect(self, ws: WebSocket) -> None:
        if ws in self._connections:
            self._connections.remove(ws)
        logger.info("websocket disconnected (total=%d)", len(self._connections))

    async def broadcast(self, event: str, data: dict) -> None:
        """向所有已连接的客户端广播事件。"""
        payload = json.dumps({"event": event, "data": data}, default=str)
        stale: list[WebSocket] = []
        for ws in self._connections:
            try:
                await ws.send_text(payload)
            except Exception:
                stale.append(ws)
        for ws in stale:
            self.disconnect(ws)

    async def broadcast_event(self, trace_id: str) -> None:
        """Collector 的 WebSocket 回调——推送 trace_updated 事件。"""
        await self.broadcast("trace_updated", {"trace_id": trace_id})

    @property
    def active_count(self) -> int:
        return len(self._connections)


# 全局单例
ws_manager = WebSocketManager()
