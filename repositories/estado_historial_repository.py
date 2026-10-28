from models.entidades import EstadoVehiculo, RegistroHistorial
from repositories.base_repository import BaseRepository


class EstadoHistorialRepository(BaseRepository):
    """Estado actual e historial de movimientos individuales."""

    LIMITE_HISTORIAL = 10

    @property
    def entidad(self) -> str:
        return "estado_historial"

    def construir(self, fila: dict) -> EstadoVehiculo:
        return EstadoVehiculo(fila)

    def obtener_estado(self, vehiculo_id: int):
        """sp_obtener_estado"""
        return self._obtener("sp_obtener_estado", (vehiculo_id,))

    def actualizar_estado(self, vehiculo_id: int, comando_id: int, origen: str):
        """sp_actualizar_estado (movimientos individuales y DEMO)."""
        self._escribir("sp_actualizar_estado", (vehiculo_id, comando_id, origen))
        return True

    def registrar_historial(self, vehiculo_id: int, comando_id: int, origen: str):
        """sp_registrar_historial (exclusivo de movimientos individuales)."""
        self._escribir("sp_registrar_historial", (vehiculo_id, comando_id, origen))
        return True

    def registrar_movimiento_atomico(self, vehiculo_id: int, comando_id: int, origen: str):
        """sp_actualizar_estado + sp_registrar_historial en UNA sola transacción."""
        params = (vehiculo_id, comando_id, origen)
        self._transaccion([("sp_actualizar_estado", params), ("sp_registrar_historial", params)])
        return True

    def obtener_historial_reciente(self, vehiculo_id: int) -> list[RegistroHistorial]:
        """sp_obtener_historial limitado a los 10 movimientos más recientes."""
        filas = self._consultar("sp_obtener_historial", (vehiculo_id,)) or []
        return [RegistroHistorial(f) for f in filas[:self.LIMITE_HISTORIAL]]
