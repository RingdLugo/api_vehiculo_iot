import asyncio
import logging
from typing import Optional

from repositories.base_repository import extraer_id
from repositories.comando_repository import ComandoRepository
from repositories.demo_repository import DemoRepository
from repositories.estado_historial_repository import EstadoHistorialRepository
from repositories.vehiculo_repository import VehiculoRepository
from ws_manager.eventos import TipoEvento
from ws_manager.manager import manager

logger = logging.getLogger(__name__)


class DemoActivaError(ValueError):
    """Ya existe una DEMO en ejecución para el vehículo (HTTP 409)."""


def _esta_activo(fila: dict) -> bool:
    return bool(fila.get("activo", True))


def _entero(valor, defecto: int) -> int:
    return int(valor) if valor is not None else defecto


class OperacionService:
    """Reglas de negocio: movimientos individuales, DEMO y control de concurrencia."""

    def __init__(self):
        self.estado_repo = EstadoHistorialRepository()
        self.vehiculo_repo = VehiculoRepository()
        self.comando_repo = ComandoRepository()
        self.demo_repo = DemoRepository()
        self.demos_activas: set[int] = set()
        self.cancelaciones: dict[int, asyncio.Event] = {}
        self._tareas: set[asyncio.Task] = set()

    # ------------------------------------------------------------------ utilidades
    async def _validar_vehiculo(self, vehiculo_id: int) -> dict:
        vehiculo = await asyncio.to_thread(self.vehiculo_repo.obtener_por_id, vehiculo_id)
        if not vehiculo:
            raise ValueError("El vehículo especificado no existe.")
        if not _esta_activo(vehiculo):
            raise ValueError("El vehículo se encuentra inactivo.")
        return vehiculo

    @staticmethod
    def _buscar_comando(comandos: list, comando_id: int) -> Optional[dict]:
        for cmd in comandos or []:
            if extraer_id(cmd, "id_comando", "id") == comando_id and _esta_activo(cmd):
                return cmd
        return None

    def tiene_demo_activa(self, vehiculo_id: int) -> bool:
        return vehiculo_id in self.demos_activas

    # ------------------------------------------------------- movimiento individual
    async def ejecutar_movimiento_individual(self, vehiculo_id: int, comando_id: int, origen: str):
        """Valida, actualiza estado + historial en UNA transacción y notifica por WebSocket."""
        await self._validar_vehiculo(vehiculo_id)

        comandos = await asyncio.to_thread(self.comando_repo.obtener_por_vehiculo, vehiculo_id)
        comando = self._buscar_comando(comandos, comando_id)
        if not comando:
            raise ValueError("El comando no existe, está inactivo o no pertenece a este vehículo.")

        try:
            await asyncio.to_thread(
                self.estado_repo.registrar_movimiento_atomico, vehiculo_id, comando_id, origen
            )
        except Exception as e:
            logger.exception("Fallo al registrar el movimiento individual")
            raise RuntimeError("Error de base de datos al registrar el movimiento.") from e

        await manager.broadcast_to_vehicle(vehiculo_id, {
            "tipo": TipoEvento.MOVIMIENTO_INDIVIDUAL,
            "comando_id": comando_id,
            "codigo": comando.get("codigo"),
            "origen": origen,
        })
        return {"mensaje": "Movimiento individual procesado y registrado en historial exitosamente."}

    # ------------------------------------------------------------------------ DEMO
    async def iniciar_demo(self, vehiculo_id: int, demo_id: int):
        """Valida y lanza la DEMO en segundo plano; responde de inmediato."""
        if vehiculo_id in self.demos_activas:
            raise DemoActivaError(
                "Ya existe una DEMO en ejecución para este vehículo. Debe finalizar o cancelarse primero."
            )

        # Se reserva el vehículo antes de cualquier await para evitar duplicados.
        self.demos_activas.add(vehiculo_id)
        try:
            await self._validar_vehiculo(vehiculo_id)

            demos = await asyncio.to_thread(self.demo_repo.obtener_demos_vehiculo, vehiculo_id)
            demo = next(
                (d for d in demos or [] if extraer_id(d, "id_demo", "id") == demo_id), None
            )
            if not demo or not _esta_activo(demo):
                raise ValueError("La DEMO no existe, está inactiva o no pertenece a este vehículo.")

            movimientos = await asyncio.to_thread(self.demo_repo.obtener_movimientos_demo, demo_id)
            if not movimientos:
                raise ValueError("La DEMO no contiene movimientos registrados.")
            movimientos = sorted(movimientos, key=lambda m: _entero(m.get("orden"), 0))

            comandos = await asyncio.to_thread(self.comando_repo.obtener_por_vehiculo, vehiculo_id)
            codigos = {extraer_id(c, "id_comando", "id"): c.get("codigo") for c in comandos or []}
        except Exception:
            self.demos_activas.discard(vehiculo_id)
            raise

        self.cancelaciones[vehiculo_id] = asyncio.Event()
        tarea = asyncio.create_task(self._ejecutar_demo(vehiculo_id, demo_id, movimientos, codigos))
        self._tareas.add(tarea)
        tarea.add_done_callback(self._tareas.discard)

        return {
            "mensaje": "DEMO iniciada. Siga el avance por WebSocket.",
            "vehiculo_id": vehiculo_id,
            "demo_id": demo_id,
            "total_movimientos": len(movimientos),
        }

    async def _ejecutar_demo(self, vehiculo_id: int, demo_id: int, movimientos: list, codigos: dict):
        """Emite los N movimientos por WebSocket. NO escribe en el historial."""
        cancelar = self.cancelaciones[vehiculo_id]
        try:
            await manager.broadcast_to_vehicle(vehiculo_id, {
                "tipo": TipoEvento.DEMO_INICIO, "demo_id": demo_id, "total_movimientos": len(movimientos),
            })

            for mov in movimientos:
                if cancelar.is_set():
                    await self._notificar_cancelacion(vehiculo_id, demo_id)
                    return

                comando_id = extraer_id(mov, "id_comando", "comando_id", "id")
                duracion_ms = _entero(mov.get("duracion_ms"), 1000)
                pausa_ms = _entero(mov.get("pausa_ms"), 500)

                # Solo actualiza el último estado; sp_registrar_historial no se invoca.
                await asyncio.to_thread(self.estado_repo.actualizar_estado, vehiculo_id, comando_id, "DEMO")

                await manager.broadcast_to_vehicle(vehiculo_id, {
                    "tipo": TipoEvento.DEMO_MOVIMIENTO,
                    "demo_id": demo_id,
                    "comando_id": comando_id,
                    "codigo": codigos.get(comando_id),
                    "orden": mov.get("orden"),
                    "duracion_ms": duracion_ms,
                    "pausa_ms": pausa_ms,
                })

                # Espera interrumpible: si llega DETENER, se despierta al instante.
                try:
                    await asyncio.wait_for(cancelar.wait(), timeout=(duracion_ms + pausa_ms) / 1000.0)
                    await self._notificar_cancelacion(vehiculo_id, demo_id)
                    return
                except asyncio.TimeoutError:
                    pass

            await manager.broadcast_to_vehicle(vehiculo_id, {"tipo": TipoEvento.DEMO_FIN, "demo_id": demo_id})

        except Exception as e:
            logger.exception("Error durante la ejecución de la DEMO %s", demo_id)
            await manager.broadcast_to_vehicle(vehiculo_id, {
                "tipo": TipoEvento.DEMO_ERROR, "demo_id": demo_id, "error": "Error interno durante la DEMO.",
            })
        finally:
            self.demos_activas.discard(vehiculo_id)
            self.cancelaciones.pop(vehiculo_id, None)

    @staticmethod
    async def _notificar_cancelacion(vehiculo_id: int, demo_id: int):
        await manager.broadcast_to_vehicle(vehiculo_id, {
            "tipo": TipoEvento.DEMO_CANCELADA,
            "demo_id": demo_id,
            "mensaje": "La DEMO fue cancelada por el usuario.",
        })

    async def cancelar_demo(self, vehiculo_id: int):
        """Acción DETENER: prioridad inmediata, interrumpe incluso la espera en curso."""
        evento = self.cancelaciones.get(vehiculo_id)
        if vehiculo_id not in self.demos_activas or evento is None:
            raise ValueError("No hay ninguna DEMO activa en este vehículo para cancelar.")
        evento.set()
        return {"mensaje": "Señal de detención enviada. La DEMO se suspenderá inmediatamente."}


# Instancia única compartida por todos los routers (el estado de DEMO vive aquí).
operacion_service = OperacionService()
