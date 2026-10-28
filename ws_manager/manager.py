import asyncio
import logging
from typing import Dict, List

from fastapi import WebSocket

from repositories.estado_historial_repository import EstadoHistorialRepository
from ws_manager.eventos import Evento, EventoConexion, EventoConsulta

logger = logging.getLogger(__name__)


class ConnectionManager:

    def __init__(self, estado_repo: EstadoHistorialRepository):
        self.__estado_repo = estado_repo
        self.__conexiones: Dict[int, List[WebSocket]] = {}

    async def connect(self, vehiculo_id: int, websocket: WebSocket):
        await websocket.accept()
        self.__conexiones.setdefault(vehiculo_id, []).append(websocket)

        try:
            ultimo = await asyncio.to_thread(self.__estado_repo.obtener_estado, vehiculo_id)
            estado = ultimo.a_diccionario() if ultimo else {"mensaje": "Sin estado previo registrado"}
        except Exception:
            logger.exception("No se pudo consultar el estado inicial del vehículo %s", vehiculo_id)
            estado = {"mensaje": "Error al consultar estado inicial"}

        await self.enviar_a_cliente(websocket, EventoConexion(vehiculo_id, estado))

    def disconnect(self, vehiculo_id: int, websocket: WebSocket):
        conexiones = self.__conexiones.get(vehiculo_id)
        if not conexiones:
            return
        if websocket in conexiones:
            conexiones.remove(websocket)
        if not conexiones:
            del self.__conexiones[vehiculo_id]

    def total_conexiones(self, vehiculo_id: int) -> int:
        return len(self.__conexiones.get(vehiculo_id, []))

    async def enviar_a_cliente(self, websocket: WebSocket, evento: Evento):
        await websocket.send_json(evento.a_diccionario())

    async def broadcast_to_vehicle(self, evento: Evento):
        """Envía el evento a todos los clientes de ese vehículo (y solo a ellos)."""
        conexiones = list(self.__conexiones.get(evento.vehiculo_id, []))
        if not conexiones:
            return

        carga = evento.a_diccionario()      # polimorfismo: cada evento arma su propio JSON
        resultados = await asyncio.gather(
            *(c.send_json(carga) for c in conexiones), return_exceptions=True
        )
        for conexion, resultado in zip(conexiones, resultados):
            if isinstance(resultado, Exception):
                self.disconnect(evento.vehiculo_id, conexion)

    async def notificar_consulta(self, vehiculo_id: int, recurso: str, datos):
        await self.broadcast_to_vehicle(EventoConsulta(vehiculo_id, recurso, datos))
