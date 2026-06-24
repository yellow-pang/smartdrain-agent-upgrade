"""
하수구 상태 WebSocket 연결을 처리하는 라우터 파일입니다.

주요 역할:
- 하수구 상태 WebSocket 엔드포인트 정의
- WebSocket 연결 등록과 해제 처리
- 수신 메시지를 개인 연결로 다시 전송
"""

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
