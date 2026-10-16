import asyncio

from fastapi import APIRouter, status

from repositories.comando_repository import ComandoRepository
from schemas.gestion_schema import ComandoActualizar, ComandoCrear
from ws_manager.manager import manager

router = APIRouter(prefix="/comandos", tags=["Comandos"])
comando_repo = ComandoRepository()


@router.get("/vehiculo/{vehiculo_id}", summary="Listar comandos de un vehículo",
            description="También se avisa por WebSocket. **SP:** `sp_obtener_comandos_vehiculo`")
async def obtener_comandos(vehiculo_id: int):
    comandos = await asyncio.to_thread(comando_repo.obtener_por_vehiculo, vehiculo_id)
    await manager.notificar_consulta(vehiculo_id, "comandos", comandos)
    return comandos


@router.post("/", status_code=status.HTTP_201_CREATED, summary="Crear comando",
             description="**SP:** `sp_crear_comando`")
def crear_comando(data: ComandoCrear):
    return comando_repo.crear(data.vehiculo_id, data.nombre, data.codigo, data.descripcion)


@router.post("/{comando_id}/actualizar", summary="Actualizar comando",
             description="**SP:** `sp_actualizar_comando`")
def actualizar_comando(comando_id: int, data: ComandoActualizar):
    return comando_repo.actualizar(comando_id, data.nombre, data.codigo, data.descripcion, data.activo)


@router.post("/{comando_id}/eliminar", summary="Eliminar comando",
             description="**SP:** `sp_eliminar_comando`")
def eliminar_comando(comando_id: int):
    return comando_repo.eliminar(comando_id)