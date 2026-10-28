import asyncio

from fastapi import status

from repositories.comando_repository import ComandoRepository
from routers.base_controller import BaseController
from schemas.gestion_schema import ComandoActualizar, ComandoCrear
from ws_manager.manager import ConnectionManager


class ComandoController(BaseController):
    """Endpoints de gestión de comandos."""

    def __init__(self, comando_repo: ComandoRepository, manager: ConnectionManager):
        self._comando_repo = comando_repo
        self._manager = manager
        super().__init__(prefix="/comandos", tags=["Comandos"])

    def _registrar_rutas(self) -> None:
        r = self._ruta
        r("/vehiculo/{vehiculo_id}", self.obtener_comandos, "GET", "Listar comandos de un vehículo",
          "También se avisa por WebSocket. **SP:** `sp_obtener_comandos_vehiculo`")
        r("/", self.crear_comando, "POST", "Crear comando", "**SP:** `sp_crear_comando`",
          status_code=status.HTTP_201_CREATED)
        r("/{comando_id}/actualizar", self.actualizar_comando, "POST", "Actualizar comando",
          "**SP:** `sp_actualizar_comando`")
        r("/{comando_id}/eliminar", self.eliminar_comando, "POST", "Eliminar comando",
          "**SP:** `sp_eliminar_comando`")

    async def obtener_comandos(self, vehiculo_id: int):
        comandos = self._serializar(
            await asyncio.to_thread(self._comando_repo.obtener_por_vehiculo, vehiculo_id))
        await self._manager.notificar_consulta(vehiculo_id, "comandos", comandos)
        return comandos

    def crear_comando(self, data: ComandoCrear):
        return self._comando_repo.crear(data.vehiculo_id, data.nombre, data.codigo, data.descripcion)

    def actualizar_comando(self, comando_id: int, data: ComandoActualizar):
        return self._comando_repo.actualizar(
            comando_id, data.nombre, data.codigo, data.descripcion, data.activo
        )

    def eliminar_comando(self, comando_id: int):
        return self._comando_repo.eliminar(comando_id)
