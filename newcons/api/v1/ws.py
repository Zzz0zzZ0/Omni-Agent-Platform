"""
WebSocket 端点 — 实时推送 ticket 处理结果等事件。
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from sqlalchemy import select

from core.database import async_session_factory
from core.models.tenant import TenantModel
from services.websocket_manager import ws_manager
from core.logger import log

router = APIRouter(tags=["websocket"])


@router.websocket("/api/v1/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(..., description="API Key for authentication"),
):
    """
    WebSocket 连接端点。
    客户端通过 ws://host/api/v1/ws?token=YOUR_API_KEY 连接。
    """
    # 鉴权
    async with async_session_factory() as session:
        result = await session.execute(
            select(TenantModel).where(
                TenantModel.api_key == token,
                TenantModel.is_active.is_(True),
            )
        )
        tenant = result.scalar_one_or_none()

    if not tenant:
        await websocket.close(code=4001, reason="Invalid API key")
        return

    tenant_id = tenant.id
    await ws_manager.connect(websocket, tenant_id)

    try:
        while True:
            # 保持连接，接收客户端心跳
            data = await websocket.receive_text()
            if data == "ping":
                await ws_manager.send_personal(websocket, "pong", {})
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket, tenant_id)
    except Exception as e:
        log.warning(f"[WS] Connection error: {e}")
        await ws_manager.disconnect(websocket, tenant_id)
