from models.entidad import Entidad


class Vehiculo(Entidad):
    @property
    def _claves_id(self) -> tuple:
        return ("id_vehiculo", "id")

    @property
    def nombre(self) -> str:
        return self.obtener("nombre", "")

    def describir(self) -> str:
        estado = "activo" if self.esta_activo() else "inactivo"
        return f"Vehículo #{self.id} '{self.nombre}' ({estado})"


class Comando(Entidad):
    @property
    def _claves_id(self) -> tuple:
        return ("id_comando", "id")

    @property
    def nombre(self) -> str:
        return self.obtener("nombre", "")

    @property
    def codigo(self):
        return self.obtener("codigo")

    def describir(self) -> str:
        return f"Comando #{self.id} '{self.nombre}' (código {self.codigo})"


class Demo(Entidad):
    @property
    def _claves_id(self) -> tuple:
        return ("id_demo", "id")

    @property
    def nombre(self) -> str:
        return self.obtener("nombre", "")

    def describir(self) -> str:
        return f"DEMO #{self.id} '{self.nombre}'"


class MovimientoDemo(Entidad):
    """Un paso de la secuencia de una DEMO."""

    DURACION_DEFECTO_MS = 1000
    PAUSA_DEFECTO_MS = 500

    @property
    def _claves_id(self) -> tuple:
        return ("id_movimiento", "id_movimiento_demo", "id")

    @property
    def comando_id(self):
        for clave in ("id_comando", "comando_id", "id"):
            valor = self.obtener(clave)
            if valor is not None:
                return valor
        return None

    @property
    def orden(self) -> int:
        return int(self.obtener("orden", 0))

    @property
    def duracion_ms(self) -> int:
        return int(self.obtener("duracion_ms", self.DURACION_DEFECTO_MS))

    @property
    def pausa_ms(self) -> int:
        return int(self.obtener("pausa_ms", self.PAUSA_DEFECTO_MS))

    def espera_total_segundos(self) -> float:
        """Método de instancia: tiempo que dura el paso incluyendo la pausa."""
        return (self.duracion_ms + self.pausa_ms) / 1000.0

    def describir(self) -> str:
        return f"Paso {self.orden}: comando {self.comando_id} ({self.duracion_ms} ms + {self.pausa_ms} ms)"


class EstadoVehiculo(Entidad):
    @property
    def _claves_id(self) -> tuple:
        return ("id_estado", "id")

    def describir(self) -> str:
        return f"Estado del vehículo {self.obtener('id_vehiculo', '?')}: comando {self.obtener('id_comando', '?')}"


class RegistroHistorial(Entidad):
    @property
    def _claves_id(self) -> tuple:
        return ("id_historial", "id")

    def describir(self) -> str:
        return f"Historial: comando {self.obtener('id_comando', '?')} desde {self.obtener('origen', '?')}"
