import asyncio
import logging
from typing import Optional

from models.entidades import Comando, MovimientoDemo
from repositories.comando_repository import ComandoRepository
from repositories.demo_repository import DemoRepository
from repositories.estado_historial_repository import EstadoHistorialRepository
from repositories.vehiculo_repository import VehiculoRepository
from ws_manager.eventos import (
    Evento, EventoDemoCancelada, EventoDemoError, EventoDemoFin, EventoDemoInicio,
    EventoDemoMovimiento, EventoMovimientoIndividual,
)
from ws_manager.manager import ConnectionManager

logger = logging.getLogger(__name__)


class DemoActivaError(ValueError):
    """Ya existe una DEMO en ejecución para el vehículo (HTTP 409)."""


class SesionDemo:
    """Objeto que representa UNA ejecución de DEMO (estado propio + métodos de instancia).

    NO escribe en el historial; solo actualiza el estado y emite eventos.
    """

    def __init__(self, vehiculo_id: int, demo_id: int, movimientos: list[MovimientoDemo],
                 codigos: dict, estado_repo: EstadoHistorialRepository, manager: ConnectionManager):
        self.__vehiculo_id = vehiculo_id
        self.__demo_id = demo_id
        self.__movimientos = movimientos
        self.__codigos = codigos
        self.__estado_repo = estado_repo
        self.__manager = manager
        self.__cancelar = asyncio.Event()

    @property
    def vehiculo_id(self) -> int:
        return self.__vehiculo_id

    @property
    def total_movimientos(self) -> int:
        return len(self.__movimientos)

    def cancelar(self) -> None:
        self.__cancelar.set()

    async def __emitir(self, evento: Evento) -> None:
        await self.__manager.broadcast_to_vehicle(evento)

    async def ejecutar(self) -> None:
        v, d = self.__vehiculo_id, self.__demo_id
        try:
            await self.__emitir(EventoDemoInicio(v, d, self.total_movimientos))

            for mov in self.__movimientos:
                if self.__cancelar.is_set():
                    await self.__emitir(EventoDemoCancelada(v, d))
                    return

                await asyncio.to_thread(self.__estado_repo.actualizar_estado, v, mov.comando_id, "DEMO")
                await self.__emitir(EventoDemoMovimiento(
                    v, d, mov.comando_id, self.__codigos.get(mov.comando_id),
                    mov.orden, mov.duracion_ms, mov.pausa_ms))

                try:
                    await asyncio.wait_for(self.__cancelar.wait(), timeout=mov.espera_total_segundos())
                    await self.__emitir(EventoDemoCancelada(v, d))
                    return
                except asyncio.TimeoutError:
                    pass

            await self.__emitir(EventoDemoFin(v, d))

        except Exception:
            logger.exception("Error durante la ejecución de la DEMO %s", d)
            await self.__emitir(EventoDemoError(v, d))


class OperacionService:
    """Reglas de negocio: movimientos individuales, DEMO y control de concurrencia."""

    def __init__(self, vehiculo_repo: VehiculoRepository, comando_repo: ComandoRepository,
                 demo_repo: DemoRepository, estado_repo: EstadoHistorialRepository,
                 manager: ConnectionManager):
        self.__vehiculo_repo = vehiculo_repo
        self.__comando_repo = comando_repo
        self.__demo_repo = demo_repo
        self.__estado_repo = estado_repo
        self.__manager = manager
        self.__sesiones: dict[int, Optional[SesionDemo]] = {}
        self.__tareas: set[asyncio.Task] = set()

    async def _validar_vehiculo(self, vehiculo_id: int):
        vehiculo = await asyncio.to_thread(self.__vehiculo_repo.obtener_por_id, vehiculo_id)
        if not vehiculo:
            raise ValueError("El vehículo especificado no existe.")
        if not vehiculo.esta_activo():
            raise ValueError("El vehículo se encuentra inactivo.")
        return vehiculo

    @staticmethod
    def _buscar_comando(comandos: list[Comando], comando_id: int) -> Optional[Comando]:
        return next((c for c in comandos if c.id == comando_id and c.esta_activo()), None)

    def tiene_demo_activa(self, vehiculo_id: int) -> bool:
        return vehiculo_id in self.__sesiones

    async def ejecutar_movimiento_individual(self, vehiculo_id: int, comando_id: int, origen: str):
        await self._validar_vehiculo(vehiculo_id)

        comandos = await asyncio.to_thread(self.__comando_repo.obtener_por_vehiculo, vehiculo_id)
        comando = self._buscar_comando(comandos, comando_id)
        if not comando:
            raise ValueError("El comando no existe, está inactivo o no pertenece a este vehículo.")

        try:
            await asyncio.to_thread(
                self.__estado_repo.registrar_movimiento_atomico, vehiculo_id, comando_id, origen
            )
        except Exception as e:
            logger.exception("Fallo al registrar el movimiento individual")
            raise RuntimeError("Error de base de datos al registrar el movimiento.") from e

        await self.__manager.broadcast_to_vehicle(
            EventoMovimientoIndividual(vehiculo_id, comando_id, comando.codigo, origen)
        )
        return {"mensaje": "Movimiento individual procesado y registrado en historial exitosamente."}

    async def iniciar_demo(self, vehiculo_id: int, demo_id: int):
        if self.tiene_demo_activa(vehiculo_id):
            raise DemoActivaError(
                "Ya existe una DEMO en ejecución para este vehículo. Debe finalizar o cancelarse primero."
            )

        self.__sesiones[vehiculo_id] = None     # reserva el cupo antes del primer await
        try:
            await self._validar_vehiculo(vehiculo_id)

            demos = await asyncio.to_thread(self.__demo_repo.obtener_demos_vehiculo, vehiculo_id)
            demo = next((d for d in demos if d.id == demo_id), None)
            if not demo or not demo.esta_activo():
                raise ValueError("La DEMO no existe, está inactiva o no pertenece a este vehículo.")

            movimientos = await asyncio.to_thread(self.__demo_repo.obtener_movimientos_demo, demo_id)
            if not movimientos:
                raise ValueError("La DEMO no contiene movimientos registrados.")
            movimientos = sorted(movimientos, key=lambda m: m.orden)

            comandos = await asyncio.to_thread(self.__comando_repo.obtener_por_vehiculo, vehiculo_id)
            codigos = {c.id: c.codigo for c in comandos}
        except Exception:
            self.__sesiones.pop(vehiculo_id, None)
            raise

        sesion = SesionDemo(vehiculo_id, demo_id, movimientos, codigos, self.__estado_repo, self.__manager)
        self.__sesiones[vehiculo_id] = sesion
        tarea = asyncio.create_task(self.__correr(sesion))
        self.__tareas.add(tarea)
        tarea.add_done_callback(self.__tareas.discard)

        return {
            "mensaje": "DEMO iniciada. Siga el avance por WebSocket.",
            "vehiculo_id": vehiculo_id,
            "demo_id": demo_id,
            "total_movimientos": sesion.total_movimientos,
        }

    async def __correr(self, sesion: SesionDemo) -> None:
        try:
            await sesion.ejecutar()
        finally:
            self.__sesiones.pop(sesion.vehiculo_id, None)

    async def cancelar_demo(self, vehiculo_id: int):
        sesion = self.__sesiones.get(vehiculo_id)
        if sesion is None:
            raise ValueError("No hay ninguna DEMO activa en este vehículo para cancelar.")
        sesion.cancelar()
        return {"mensaje": "Señal de detención enviada. La DEMO se suspenderá inmediatamente."}
