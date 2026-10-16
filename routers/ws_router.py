import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ws_manager.manager import manager

router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws/vehiculo/{vehiculo_id}")
async def websocket_vehiculo(websocket: WebSocket, vehiculo_id: int):
    """Canal WebSocket para monitorear un vehículo (movimientos y DEMO en tiempo real).

    El estado inicial lo envía `manager.connect` (evento `conexion_establecida`).
    """
    await manager.connect(vehiculo_id, websocket)
    try:
        while True:
            texto = await websocket.receive_text()
            if texto.strip().lower() == "ping":
                await websocket.send_json({
                    "tipo": "pong",
                    "vehiculo_id": vehiculo_id,
                    "marca_temporal": datetime.datetime.now().isoformat(),
                })
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(vehiculo_id, websocket)
