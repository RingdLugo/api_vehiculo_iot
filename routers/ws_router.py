import asyncio
import logging

from fastapi import WebSocket, WebSocketDisconnect

from repositories.vehiculo_repository import VehiculoRepository
from routers.base_controller import BaseController
from ws_manager.eventos import EventoEco
from ws_manager.manager import ConnectionManager

logger = logging.getLogger(__name__)


class WebSocketController(BaseController):
    """Canal WebSocket para monitorear un vehículo en tiempo real."""

    def __init__(self, vehiculo_repo: VehiculoRepository, manager: ConnectionManager):
        self._vehiculo_repo = vehiculo_repo
        self._manager = manager
        super().__init__(prefix="", tags=["WebSocket"])

    def _registrar_rutas(self) -> None:
        self._router.add_api_websocket_route("/ws/vehiculo/{vehiculo_id}", self.websocket_vehiculo)

    async def websocket_vehiculo(self, websocket: WebSocket, vehiculo_id: int):
        """Eventos: conexion_establecida, eco_cliente_ws, consulta, movimiento_individual,
        demo_inicio, demo_movimiento, demo_fin, demo_cancelada y demo_error."""
        try:
            vehiculo = await asyncio.to_thread(self._vehiculo_repo.obtener_por_id, vehiculo_id)
        except Exception:
            logger.exception("No se pudo validar el vehículo %s en el WebSocket", vehiculo_id)
            await websocket.close(code=1011)
            return
        if not vehiculo:
            await websocket.close(code=1008)
            return

        await self._manager.connect(vehiculo_id, websocket)
        try:
            while True:
                texto = await websocket.receive_text()
                logger.info("Mensaje recibido del vehículo %s: %s", vehiculo_id, texto)
                await self._manager.enviar_a_cliente(websocket, EventoEco(vehiculo_id, texto))
        except WebSocketDisconnect:
            pass
        finally:
            self._manager.disconnect(vehiculo_id, websocket)
