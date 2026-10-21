import asyncio
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from repositories.vehiculo_repository import VehiculoRepository
from ws_manager.eventos import TipoEvento
from ws_manager.manager import manager

logger = logging.getLogger(__name__)

router = APIRouter(tags=["WebSocket"])
vehiculo_repo = VehiculoRepository()


@router.websocket("/ws/vehiculo/{vehiculo_id}")
async def websocket_vehiculo(websocket: WebSocket, vehiculo_id: int):
    """Canal WebSocket para monitorear un vehículo y recibir mensajes en tiempo real desde el cliente.

    Eventos que envía el servidor: conexion_establecida, eco_cliente_ws,
    demo_inicio, demo_movimiento, demo_fin, demo_cancelada y demo_error.
    """
    try:
        vehiculo = await asyncio.to_thread(vehiculo_repo.obtener_por_id, vehiculo_id)
    except Exception:
        logger.exception("No se pudo validar el vehículo %s en el WebSocket", vehiculo_id)
        await websocket.close(code=1011)
        return
    if not vehiculo:
        await websocket.close(code=1008)
        return

    await manager.connect(vehiculo_id, websocket)
    try:
        while True:
            texto_enviado = await websocket.receive_text()
            
            logger.info("Mensaje recibido por WebSocket del vehículo %s: %s", vehiculo_id, texto_enviado)

            await websocket.send_json({
                "tipo": "eco_cliente_ws",
                "vehiculo_id": vehiculo_id,
                "mensaje_recibido": texto_enviado,
                "estado": "Procesado correctamente por el servidor"
            })
            
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(vehiculo_id, websocket)
