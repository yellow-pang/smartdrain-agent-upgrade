from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.websocket.manager import manager

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/drains/status")
async def drain_status_websocket(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            message = await websocket.receive_text()
            await manager.send_personal_message(message, websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
