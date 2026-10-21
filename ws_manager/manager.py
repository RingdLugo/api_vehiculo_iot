import asyncio
import logging
from typing import Dict, List

from fastapi import WebSocket

from repositories.estado_historial_repository import EstadoHistorialRepository
from repositories.comando_repository import ComandoRepository
from ws_manager.eventos import TipoEvento, construir_evento

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Administra las conexiones WebSocket agrupadas por vehículo.

    Cada vehículo tiene su propia lista de conexiones, así un cliente solo
    recibe los eventos del vehículo que monitorea.
    """

    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}
        self.estado_repo = EstadoHistorialRepository()
        self.comando_repo = ComandoRepository()

    async def connect(self, vehiculo_id: int, websocket: WebSocket):
        """Acepta la conexión, la registra y envía únicamente el estado inicial más reciente."""
        await websocket.accept()
        self.active_connections.setdefault(vehiculo_id, []).append(websocket)

        try:
            ultimo = await asyncio.to_thread(self.estado_repo.obtener_estado, vehiculo_id)
            estado_inicial = ultimo if ultimo else {"mensaje": "Sin estado previo registrado"}
        except Exception:
            logger.exception("No se pudo consultar el estado inicial del vehículo %s", vehiculo_id)
            estado_inicial = {"mensaje": "Error al consultar estado inicial"}

        await websocket.send_json(
            construir_evento(
                TipoEvento.CONEXION_ESTABLECIDA, 
                vehiculo_id, 
                estado_inicial=estado_inicial
            )
        )

    def disconnect(self, vehiculo_id: int, websocket: WebSocket):
        """Quita la conexión sin afectar a los demás clientes."""
        conexiones = self.active_connections.get(vehiculo_id)
        if not conexiones:
            return
        if websocket in conexiones:
            conexiones.remove(websocket)
        if not conexiones:
            del self.active_connections[vehiculo_id]

    def total_conexiones(self, vehiculo_id: int) -> int:
        """Cuántos clientes están monitoreando ese vehículo."""
        return len(self.active_connections.get(vehiculo_id, []))

    async def enviar_a_cliente(self, websocket: WebSocket, tipo: str, vehiculo_id: int, **datos):
        """Envía un evento a un solo cliente (por ejemplo, la respuesta a un ping)."""
        await websocket.send_json(construir_evento(tipo, vehiculo_id, **datos))

    async def broadcast_to_vehicle(self, vehiculo_id: int, mensaje: dict):
        """Envía el evento a todos los clientes de ese vehículo (y solo a ellos).

        `mensaje` debe traer la clave "tipo". Si un cliente falla, se
        desconecta sin afectar a los demás.
        """
        conexiones = list(self.active_connections.get(vehiculo_id, []))
        if not conexiones:
            return

        datos = dict(mensaje)
        tipo = datos.pop("tipo", "movimiento")
        datos.pop("vehiculo_id", None)
        evento = construir_evento(tipo, vehiculo_id, **datos)

        resultados = await asyncio.gather(
            *(conexion.send_json(evento) for conexion in conexiones),
            return_exceptions=True,
        )
        for conexion, resultado in zip(conexiones, resultados):
            if isinstance(resultado, Exception):
                self.disconnect(vehiculo_id, conexion)


manager = ConnectionManager()