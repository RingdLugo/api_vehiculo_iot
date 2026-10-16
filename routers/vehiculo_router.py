import logging

from fastapi import APIRouter, HTTPException, status

from repositories.comando_repository import ComandoRepository
from repositories.demo_repository import DemoRepository
from repositories.estado_historial_repository import EstadoHistorialRepository
from repositories.vehiculo_repository import VehiculoRepository
from schemas.gestion_schema import VehiculoActualizar, VehiculoCrear
from schemas.movimiento_schema import DemoRequest, MovimientoIndividualRequest
from services.operacion_service import DemoActivaError, operacion_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/vehiculos", tags=["Vehículos y Operaciones"])

vehiculo_repo = VehiculoRepository()
comando_repo = ComandoRepository()
estado_repo = EstadoHistorialRepository()
demo_repo = DemoRepository()


def _vehiculo_o_404(vehiculo_id: int) -> dict:
    vehiculo = vehiculo_repo.obtener_por_id(vehiculo_id)
    if not vehiculo:
        raise HTTPException(status_code=404, detail="Vehículo no encontrado")
    return vehiculo


# ------------------------------------------------------------------ GET
@router.get("/", summary="Listar todos los vehículos",
            description="Listado completo de vehículos. **SP:** `sp_obtener_vehiculos`")
def obtener_vehiculos():
    return vehiculo_repo.obtener_todos()


@router.get("/{vehiculo_id}", summary="Obtener vehículo por ID",
            description="Información de un vehículo. **SP:** `sp_obtener_vehiculo`",
            responses={404: {"description": "Vehículo no encontrado."}})
def obtener_vehiculo(vehiculo_id: int):
    return _vehiculo_o_404(vehiculo_id)


@router.get("/{vehiculo_id}/estado", summary="Consultar último estado del vehículo",
            description="Último estado registrado. **SP:** `sp_obtener_estado`",
            responses={404: {"description": "Estado no encontrado para este vehículo."}})
def obtener_estado_vehiculo(vehiculo_id: int):
    estado = estado_repo.obtener_estado(vehiculo_id)
    if not estado:
        raise HTTPException(status_code=404, detail="Estado no encontrado para este vehículo")
    return estado


@router.get("/{vehiculo_id}/historial", summary="Consultar historial reciente",
            description="Los 10 movimientos individuales más recientes. **SP:** `sp_obtener_historial`",
            responses={200: {"description": "Historial (máximo 10 registros)."}})
def obtener_historial_vehiculo(vehiculo_id: int):
    return estado_repo.obtener_historial_reciente(vehiculo_id)


@router.get("/{vehiculo_id}/detalle-completo", summary="Detalle completo del vehículo",
            description="Vehículo, comandos disponibles, último estado y DEMOs asociadas en una respuesta.",
            responses={404: {"description": "Vehículo no encontrado."}})
def obtener_detalle_completo_vehiculo(vehiculo_id: int):
    vehiculo = _vehiculo_o_404(vehiculo_id)
    estado = estado_repo.obtener_estado(vehiculo_id)
    return {
        "vehiculo": vehiculo,
        "estado_actual": estado if estado else "Sin estado registrado",
        "comandos_disponibles": comando_repo.obtener_por_vehiculo(vehiculo_id),
        "demos_asociadas": demo_repo.obtener_demos_vehiculo(vehiculo_id),
    }


# ----------------------------------------------------------- POST: gestión
@router.post("/", status_code=status.HTTP_201_CREATED, summary="Crear vehículo",
             description="Registra un vehículo. **SP:** `sp_crear_vehiculo`")
def crear_vehiculo(data: VehiculoCrear):
    return vehiculo_repo.crear(data.nombre, data.descripcion)


@router.post("/{vehiculo_id}/actualizar", summary="Actualizar vehículo",
             description="Modifica nombre, descripción y estado activo. **SP:** `sp_actualizar_vehiculo`",
             responses={404: {"description": "Vehículo no encontrado."}})
def actualizar_vehiculo(vehiculo_id: int, data: VehiculoActualizar):
    _vehiculo_o_404(vehiculo_id)
    return vehiculo_repo.actualizar(vehiculo_id, data.nombre, data.descripcion, data.activo)


@router.post("/{vehiculo_id}/eliminar", summary="Eliminar vehículo",
             description="Elimina un vehículo. **SP:** `sp_eliminar_vehiculo`",
             responses={404: {"description": "Vehículo no encontrado."},
                        409: {"description": "El vehículo tiene una DEMO en ejecución."}})
def eliminar_vehiculo(vehiculo_id: int):
    _vehiculo_o_404(vehiculo_id)
    if operacion_service.tiene_demo_activa(vehiculo_id):
        raise HTTPException(status_code=409, detail="El vehículo tiene una DEMO en ejecución.")
    return vehiculo_repo.eliminar(vehiculo_id)


# ------------------------------------------------- POST: operaciones
@router.post("/{vehiculo_id}/movimiento", status_code=status.HTTP_201_CREATED,
             summary="Ejecutar movimiento individual",
             description=("Valida vehículo y comando, y en UNA transacción actualiza el estado y registra el "
                          "historial; luego notifica por WebSocket. **SP:** `sp_actualizar_estado`, "
                          "`sp_registrar_historial`"),
             responses={201: {"description": "Movimiento ejecutado y registrado."},
                        400: {"description": "Datos inválidos, vehículo inactivo o comando no autorizado."},
                        500: {"description": "Error interno en la base de datos."}})
async def registrar_movimiento_individual(vehiculo_id: int, data: MovimientoIndividualRequest):
    try:
        return await operacion_service.ejecutar_movimiento_individual(vehiculo_id, data.comando_id, data.origen)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        logger.exception("Error en movimiento individual")
        raise HTTPException(status_code=500, detail="Error interno al procesar el movimiento.")


@router.post("/{vehiculo_id}/demo/iniciar", status_code=status.HTTP_200_OK,
             summary="Iniciar ejecución de DEMO",
             description=("Valida y lanza la secuencia de N movimientos en segundo plano; responde de inmediato y "
                          "el avance se emite por WebSocket. No escribe en el historial. "
                          "**SP:** `sp_obtener_demos`, `sp_obtener_movimientos_demo`, `sp_actualizar_estado`"),
             responses={200: {"description": "DEMO iniciada."},
                        400: {"description": "DEMO inexistente, ajena al vehículo o sin movimientos."},
                        409: {"description": "Ya existe una DEMO activa para este vehículo."},
                        500: {"description": "Error interno."}})
async def iniciar_demo(vehiculo_id: int, data: DemoRequest):
    try:
        return await operacion_service.iniciar_demo(vehiculo_id, data.demo_id)
    except DemoActivaError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        logger.exception("Error al iniciar la DEMO")
        raise HTTPException(status_code=500, detail="Error interno al iniciar la DEMO.")


@router.post("/{vehiculo_id}/demo/detener", summary="Cancelar DEMO en curso",
             description="Cancela de inmediato la DEMO activa del vehículo (interrumpe incluso la espera en curso).",
             responses={200: {"description": "Señal de detención enviada."},
                        400: {"description": "No hay ninguna DEMO activa."}})
async def detener_demo(vehiculo_id: int):
    try:
        return await operacion_service.cancelar_demo(vehiculo_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
