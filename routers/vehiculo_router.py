import logging

from fastapi import HTTPException, status

from repositories.comando_repository import ComandoRepository
from repositories.demo_repository import DemoRepository
from repositories.estado_historial_repository import EstadoHistorialRepository
from repositories.vehiculo_repository import VehiculoRepository
from routers.base_controller import BaseController
from schemas.gestion_schema import VehiculoActualizar, VehiculoCrear
from schemas.movimiento_schema import DemoRequest, MovimientoIndividualRequest
from services.operacion_service import DemoActivaError, OperacionService

logger = logging.getLogger(__name__)


class VehiculoController(BaseController):
    """Endpoints de vehículos, movimientos individuales y control de DEMO."""

    def __init__(self, vehiculo_repo: VehiculoRepository, comando_repo: ComandoRepository,
                 estado_repo: EstadoHistorialRepository, demo_repo: DemoRepository,
                 operacion_service: OperacionService):
        self._vehiculo_repo = vehiculo_repo
        self._comando_repo = comando_repo
        self._estado_repo = estado_repo
        self._demo_repo = demo_repo
        self._operacion = operacion_service
        super().__init__(prefix="/vehiculos", tags=["Vehículos y Operaciones"])

    def _vehiculo_o_404(self, vehiculo_id: int) -> dict:
        vehiculo = self._vehiculo_repo.obtener_por_id(vehiculo_id)
        if not vehiculo:
            raise HTTPException(status_code=404, detail="Vehículo no encontrado")
        return vehiculo

    def _registrar_rutas(self) -> None:
        r = self._ruta
        r("/", self.obtener_vehiculos, "GET", "Listar todos los vehículos",
          "Listado completo de vehículos. **SP:** `sp_obtener_vehiculos`")
        r("/{vehiculo_id}", self.obtener_vehiculo, "GET", "Obtener vehículo por ID",
          "**SP:** `sp_obtener_vehiculo`", responses={404: {"description": "Vehículo no encontrado."}})
        r("/{vehiculo_id}/estado", self.obtener_estado, "GET", "Consultar último estado del vehículo",
          "**SP:** `sp_obtener_estado`", responses={404: {"description": "Estado no encontrado."}})
        r("/{vehiculo_id}/historial", self.obtener_historial, "GET", "Consultar historial reciente",
          "Los 10 movimientos individuales más recientes. **SP:** `sp_obtener_historial`")
        r("/{vehiculo_id}/detalle-completo", self.obtener_detalle_completo, "GET",
          "Detalle completo del vehículo",
          "Vehículo, comandos, último estado y DEMOs asociadas en una respuesta.",
          responses={404: {"description": "Vehículo no encontrado."}})
        r("/", self.crear_vehiculo, "POST", "Crear vehículo", "**SP:** `sp_crear_vehiculo`",
          status_code=status.HTTP_201_CREATED)
        r("/{vehiculo_id}/actualizar", self.actualizar_vehiculo, "POST", "Actualizar vehículo",
          "**SP:** `sp_actualizar_vehiculo`", responses={404: {"description": "Vehículo no encontrado."}})
        r("/{vehiculo_id}/eliminar", self.eliminar_vehiculo, "POST", "Eliminar vehículo",
          "**SP:** `sp_eliminar_vehiculo`",
          responses={404: {"description": "Vehículo no encontrado."},
                     409: {"description": "El vehículo tiene una DEMO en ejecución."}})
        r("/{vehiculo_id}/movimiento", self.registrar_movimiento_individual, "POST",
          "Ejecutar movimiento individual",
          "Valida, actualiza estado e historial en UNA transacción y notifica por WebSocket.",
          status_code=status.HTTP_201_CREATED,
          responses={400: {"description": "Datos inválidos o comando no autorizado."},
                     500: {"description": "Error interno en la base de datos."}})
        r("/{vehiculo_id}/demo/iniciar", self.iniciar_demo, "POST", "Iniciar ejecución de DEMO",
          "Lanza la secuencia en segundo plano; el avance se emite por WebSocket.",
          status_code=status.HTTP_200_OK,
          responses={400: {"description": "DEMO inexistente o sin movimientos."},
                     409: {"description": "Ya existe una DEMO activa."}})
        r("/{vehiculo_id}/demo/detener", self.detener_demo, "POST", "Cancelar DEMO en curso",
          "Cancela de inmediato la DEMO activa del vehículo.",
          responses={400: {"description": "No hay ninguna DEMO activa."}})

    # ---------- consultas ----------
    def obtener_vehiculos(self):
        return self._serializar(self._vehiculo_repo.obtener_todos())

    def obtener_vehiculo(self, vehiculo_id: int):
        return self._serializar(self._vehiculo_o_404(vehiculo_id))

    def obtener_estado(self, vehiculo_id: int):
        estado = self._estado_repo.obtener_estado(vehiculo_id)
        if not estado:
            raise HTTPException(status_code=404, detail="Estado no encontrado para este vehículo")
        return self._serializar(estado)

    def obtener_historial(self, vehiculo_id: int):
        return self._serializar(self._estado_repo.obtener_historial_reciente(vehiculo_id))

    def obtener_detalle_completo(self, vehiculo_id: int):
        vehiculo = self._vehiculo_o_404(vehiculo_id)
        estado = self._estado_repo.obtener_estado(vehiculo_id)
        return {
            "vehiculo": self._serializar(vehiculo),
            "estado_actual": self._serializar(estado) if estado else "Sin estado registrado",
            "comandos_disponibles": self._serializar(self._comando_repo.obtener_por_vehiculo(vehiculo_id)),
            "demos_asociadas": self._serializar(self._demo_repo.obtener_demos_vehiculo(vehiculo_id)),
        }

    # ---------- gestión ----------
    def crear_vehiculo(self, data: VehiculoCrear):
        return self._vehiculo_repo.crear(data.nombre, data.descripcion)

    def actualizar_vehiculo(self, vehiculo_id: int, data: VehiculoActualizar):
        self._vehiculo_o_404(vehiculo_id)
        return self._vehiculo_repo.actualizar(vehiculo_id, data.nombre, data.descripcion, data.activo)

    def eliminar_vehiculo(self, vehiculo_id: int):
        self._vehiculo_o_404(vehiculo_id)
        if self._operacion.tiene_demo_activa(vehiculo_id):
            raise HTTPException(status_code=409, detail="El vehículo tiene una DEMO en ejecución.")
        return self._vehiculo_repo.eliminar(vehiculo_id)

    # ---------- operaciones ----------
    async def registrar_movimiento_individual(self, vehiculo_id: int, data: MovimientoIndividualRequest):
        try:
            return await self._operacion.ejecutar_movimiento_individual(
                vehiculo_id, data.comando_id, data.origen
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception:
            logger.exception("Error en movimiento individual")
            raise HTTPException(status_code=500, detail="Error interno al procesar el movimiento.")

    async def iniciar_demo(self, vehiculo_id: int, data: DemoRequest):
        try:
            return await self._operacion.iniciar_demo(vehiculo_id, data.demo_id)
        except DemoActivaError as e:
            raise HTTPException(status_code=409, detail=str(e))
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception:
            logger.exception("Error al iniciar la DEMO")
            raise HTTPException(status_code=500, detail="Error interno al iniciar la DEMO.")

    async def detener_demo(self, vehiculo_id: int):
        try:
            return await self._operacion.cancelar_demo(vehiculo_id)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
