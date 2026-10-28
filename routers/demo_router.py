import asyncio

from fastapi import status

from repositories.demo_repository import DemoRepository
from routers.base_controller import BaseController
from schemas.gestion_schema import (
    DemoActualizar, DemoCrear, MovimientoDemoActualizar, MovimientoDemoCrear,
)
from ws_manager.manager import ConnectionManager


class DemoController(BaseController):
    """Endpoints de gestión de DEMOs y sus movimientos."""

    def __init__(self, demo_repo: DemoRepository, manager: ConnectionManager):
        self._demo_repo = demo_repo
        self._manager = manager
        super().__init__(prefix="/demos", tags=["DEMO"])

    def _registrar_rutas(self) -> None:
        r = self._ruta
        created = status.HTTP_201_CREATED
        r("/vehiculo/{vehiculo_id}", self.obtener_demos, "GET", "Listar DEMOs de un vehículo",
          "También se avisa por WebSocket. **SP:** `sp_obtener_demos`")
        r("/{demo_id}/movimientos", self.obtener_movimientos, "GET", "Listar movimientos de una DEMO",
          "Secuencia de N movimientos. **SP:** `sp_obtener_movimientos_demo`")
        r("/", self.crear_demo, "POST", "Crear DEMO", "**SP:** `sp_crear_demo`", status_code=created)
        r("/{demo_id}/actualizar", self.actualizar_demo, "POST", "Actualizar DEMO",
          "**SP:** `sp_actualizar_demo`")
        r("/{demo_id}/eliminar", self.eliminar_demo, "POST", "Eliminar DEMO",
          "**SP:** `sp_eliminar_demo`")
        r("/{demo_id}/movimientos", self.agregar_movimiento, "POST", "Agregar movimiento a una DEMO",
          "**SP:** `sp_agregar_movimiento_demo`", status_code=created)
        r("/movimientos/{movimiento_id}/actualizar", self.actualizar_movimiento, "POST",
          "Actualizar movimiento de DEMO", "**SP:** `sp_actualizar_movimiento_demo`")
        r("/movimientos/{movimiento_id}/eliminar", self.eliminar_movimiento, "POST",
          "Eliminar movimiento de DEMO", "**SP:** `sp_eliminar_movimiento_demo`")

    async def obtener_demos(self, vehiculo_id: int):
        demos = self._serializar(
            await asyncio.to_thread(self._demo_repo.obtener_demos_vehiculo, vehiculo_id))
        await self._manager.notificar_consulta(vehiculo_id, "demos", demos)
        return demos

    def obtener_movimientos(self, demo_id: int):
        return self._serializar(self._demo_repo.obtener_movimientos_demo(demo_id))

    def crear_demo(self, data: DemoCrear):
        return self._demo_repo.crear_demo(data.vehiculo_id, data.nombre, data.descripcion)

    def actualizar_demo(self, demo_id: int, data: DemoActualizar):
        return self._demo_repo.actualizar_demo(demo_id, data.nombre, data.descripcion, data.activo)

    def eliminar_demo(self, demo_id: int):
        return self._demo_repo.eliminar(demo_id)

    def agregar_movimiento(self, demo_id: int, data: MovimientoDemoCrear):
        return self._demo_repo.agregar_movimiento_demo(
            demo_id, data.comando_id, data.orden, data.duracion_ms, data.pausa_ms
        )

    def actualizar_movimiento(self, movimiento_id: int, data: MovimientoDemoActualizar):
        return self._demo_repo.actualizar_movimiento_demo(
            movimiento_id, data.comando_id, data.orden, data.duracion_ms, data.pausa_ms
        )

    def eliminar_movimiento(self, movimiento_id: int):
        return self._demo_repo.eliminar_movimiento_demo(movimiento_id)
