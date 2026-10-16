import asyncio
import datetime
from typing import Dict, List

from fastapi import WebSocket
from fastapi.encoders import jsonable_encoder

from repositories.estado_historial_repository import EstadoHistorialRepository


class ConnectionManager:
    """Administra las conexiones WebSocket agrupadas por vehículo."""

    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}
        self.estado_repo = EstadoHistorialRepository()

    @staticmethod
    def _ahora() -> str:
        return datetime.datetime.now().isoformat()

    async def connect(self, vehiculo_id: int, websocket: WebSocket):
        """Acepta la conexión, la registra y envía UNA sola vez el último estado."""
        await websocket.accept()
        self.active_connections.setdefault(vehiculo_id, []).append(websocket)

        try:
            ultimo = await asyncio.to_thread(self.estado_repo.obtener_estado, vehiculo_id)
            estado_inicial = ultimo if ultimo else {"mensaje": "Sin estado previo registrado"}
        except Exception:
            estado_inicial = {"mensaje": "Error al consultar estado inicial"}

        await websocket.send_json(jsonable_encoder({
            "tipo": "conexion_establecida",
            "vehiculo_id": vehiculo_id,
            "estado_inicial": estado_inicial,
            "marca_temporal": self._ahora(),
        }))

    def disconnect(self, vehiculo_id: int, websocket: WebSocket):
        """Quita la conexión sin afectar a los demás clientes."""
        conexiones = self.active_connections.get(vehiculo_id)
        if not conexiones:
            return
        if websocket in conexiones:
            conexiones.remove(websocket)
        if not conexiones:
            del self.active_connections[vehiculo_id]

    async def broadcast_to_vehicle(self, vehiculo_id: int, mensaje: dict):
        """Envía el evento solo a los clientes que monitorean ese vehículo."""
        conexiones = self.active_connections.get(vehiculo_id)
        if not conexiones:
            return

        completo = jsonable_encoder({
            "tipo": "movimiento",
            "vehiculo_id": vehiculo_id,
            "comando_id": None,
            "codigo": None,
            "marca_temporal": self._ahora(),
            **mensaje,
        })

        for conexion in list(conexiones):
            try:
                await conexion.send_json(completo)
            except Exception:
                self.disconnect(vehiculo_id, conexion)


manager = ConnectionManager()
