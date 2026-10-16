import asyncio

from fastapi import APIRouter, status

from repositories.demo_repository import DemoRepository
from schemas.gestion_schema import (
    DemoActualizar, DemoCrear, MovimientoDemoActualizar, MovimientoDemoCrear,
)
from ws_manager.manager import manager

router = APIRouter(prefix="/demos", tags=["DEMO"])
demo_repo = DemoRepository()


@router.get("/vehiculo/{vehiculo_id}", summary="Listar DEMOs de un vehículo",
            description="También se avisa por WebSocket. **SP:** `sp_obtener_demos`")
async def obtener_demos(vehiculo_id: int):
    demos = await asyncio.to_thread(demo_repo.obtener_demos_vehiculo, vehiculo_id)
    await manager.notificar_consulta(vehiculo_id, "demos", demos)
    return demos


@router.get("/{demo_id}/movimientos", summary="Listar movimientos de una DEMO",
            description="Secuencia de N movimientos (orden, duración y pausa). **SP:** `sp_obtener_movimientos_demo`")
def obtener_movimientos(demo_id: int):
    return demo_repo.obtener_movimientos_demo(demo_id)


@router.post("/", status_code=status.HTTP_201_CREATED, summary="Crear DEMO",
             description="**SP:** `sp_crear_demo`")
def crear_demo(data: DemoCrear):
    return demo_repo.crear_demo(data.vehiculo_id, data.nombre, data.descripcion)


@router.post("/{demo_id}/actualizar", summary="Actualizar DEMO",
             description="**SP:** `sp_actualizar_demo`")
def actualizar_demo(demo_id: int, data: DemoActualizar):
    return demo_repo.actualizar_demo(demo_id, data.nombre, data.descripcion, data.activo)


@router.post("/{demo_id}/eliminar", summary="Eliminar DEMO",
             description="**SP:** `sp_eliminar_demo`")
def eliminar_demo(demo_id: int):
    return demo_repo.eliminar_demo(demo_id)


@router.post("/{demo_id}/movimientos", status_code=status.HTTP_201_CREATED,
             summary="Agregar movimiento a una DEMO",
             description="**SP:** `sp_agregar_movimiento_demo`")
def agregar_movimiento(demo_id: int, data: MovimientoDemoCrear):
    return demo_repo.agregar_movimiento_demo(demo_id, data.comando_id, data.orden, data.duracion_ms, data.pausa_ms)


@router.post("/movimientos/{movimiento_id}/actualizar", summary="Actualizar movimiento de DEMO",
             description="**SP:** `sp_actualizar_movimiento_demo`")
def actualizar_movimiento(movimiento_id: int, data: MovimientoDemoActualizar):
    return demo_repo.actualizar_movimiento_demo(
        movimiento_id, data.comando_id, data.orden, data.duracion_ms, data.pausa_ms
    )


@router.post("/movimientos/{movimiento_id}/eliminar", summary="Eliminar movimiento de DEMO",
             description="**SP:** `sp_eliminar_movimiento_demo`")
def eliminar_movimiento(movimiento_id: int):
    return demo_repo.eliminar_movimiento_demo(movimiento_id)