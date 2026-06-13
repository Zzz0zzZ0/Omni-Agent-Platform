"""
WebSocket 连接管理器 — 按 tenant 隔离的实时推送。
"""
import asyncio
import json
from typing import Dict, Set
from fastapi import WebSocket
from core.logger import log


class ConnectionManager:
    """管理 WebSocket 连接，支持 per-tenant 广播"""

    def __init__(self):
        # tenant_id -> set of active connections
        self._connections: Dict[str, Set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, tenant_id: str) -> None:
        await websocket.accept()
        async with self._lock:
            if tenant_id not in self._connections:
                self._connections[tenant_id] = set()
            self._connections[tenant_id].add(websocket)
        log.info(f"[WS] Client connected for tenant {tenant_id}. Total: {len(self._connections.get(tenant_id, set()))}")

    async def disconnect(self, websocket: WebSocket, tenant_id: str) -> None:
        async with self._lock:
            if tenant_id in self._connections:
                self._connections[tenant_id].discard(websocket)
                if not self._connections[tenant_id]:
                    del self._connections[tenant_id]
        log.info(f"[WS] Client disconnected from tenant {tenant_id}")

    async def broadcast(self, tenant_id: str, event_type: str, data: dict) -> None:
        """向指定 tenant 的所有连接广播消息"""
        message = json.dumps({"type": event_type, "data": data}, ensure_ascii=False)
        async with self._lock:
            connections = self._connections.get(tenant_id, set()).copy()

        dead = []
        for ws in connections:
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)

        if dead:
            async with self._lock:
                for ws in dead:
                    self._connections.get(tenant_id, set()).discard(ws)

    async def send_personal(self, websocket: WebSocket, event_type: str, data: dict) -> None:
        """向单个连接发送消息"""
        message = json.dumps({"type": event_type, "data": data}, ensure_ascii=False)
        try:
            await websocket.send_text(message)
        except Exception as e:
            log.warning(f"[WS] Failed to send personal message: {e}")


# 全局单例 (WebSocket 管理器本身是进程级的，tenant 隔离在逻辑层面)
ws_manager = ConnectionManager()
