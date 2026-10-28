import datetime
from abc import ABC, abstractmethod
from typing import Optional

from fastapi.encoders import jsonable_encoder


class Evento(ABC):
    def __init__(self, vehiculo_id: int, comando_id: Optional[int] = None, codigo=None):
        self.__vehiculo_id = vehiculo_id
        self.__comando_id = comando_id
        self.__codigo = codigo
        self.__marca_temporal = datetime.datetime.now().isoformat()

    @property
    @abstractmethod
    def tipo(self) -> str:
        """Nombre del evento que recibe el cliente."""

    @property
    def vehiculo_id(self) -> int:
        return self.__vehiculo_id

    @property
    def marca_temporal(self) -> str:
        return self.__marca_temporal

    def _datos_extra(self) -> dict:
        """Campos propios de cada evento. Las subclases lo SOBRESCRIBEN."""
        return {}

    def a_diccionario(self) -> dict:
        evento = {
            "tipo": self.tipo,
            "vehiculo_id": self.__vehiculo_id,
            "comando_id": self.__comando_id,
            "codigo": self.__codigo,
            "marca_temporal": self.__marca_temporal,
        }
        evento.update(self._datos_extra())
        return jsonable_encoder(evento)


class EventoConexion(Evento):
    def __init__(self, vehiculo_id: int, estado_inicial: dict):
        super().__init__(vehiculo_id)
        self.__estado_inicial = estado_inicial

    @property
    def tipo(self) -> str:
        return "conexion_establecida"

    def _datos_extra(self) -> dict:
        return {"estado_inicial": self.__estado_inicial}


class EventoMovimientoIndividual(Evento):
    def __init__(self, vehiculo_id: int, comando_id: int, codigo, origen: str):
        super().__init__(vehiculo_id, comando_id, codigo)
        self.__origen = origen

    @property
    def tipo(self) -> str:
        return "movimiento_individual"

    def _datos_extra(self) -> dict:
        return {"origen": self.__origen}


class EventoConsulta(Evento):
    def __init__(self, vehiculo_id: int, recurso: str, datos):
        super().__init__(vehiculo_id)
        self.__recurso = recurso
        self.__datos = datos

    @property
    def tipo(self) -> str:
        return "consulta"

    def _datos_extra(self) -> dict:
        return {"recurso": self.__recurso, "datos": self.__datos}


class EventoEco(Evento):
    def __init__(self, vehiculo_id: int, mensaje_recibido: str):
        super().__init__(vehiculo_id)
        self.__mensaje = mensaje_recibido

    @property
    def tipo(self) -> str:
        return "eco_cliente_ws"

    def _datos_extra(self) -> dict:
        return {"mensaje_recibido": self.__mensaje, "estado": "Procesado correctamente por el servidor"}


class EventoDemo(Evento, ABC):
    """Clase intermedia abstracta: todo evento de DEMO lleva `demo_id` (herencia multinivel)."""

    def __init__(self, vehiculo_id: int, demo_id: int, comando_id=None, codigo=None):
        super().__init__(vehiculo_id, comando_id, codigo)
        self.__demo_id = demo_id

    def _datos_extra(self) -> dict:
        return {"demo_id": self.__demo_id}


class EventoDemoInicio(EventoDemo):
    def __init__(self, vehiculo_id: int, demo_id: int, total_movimientos: int):
        super().__init__(vehiculo_id, demo_id)
        self.__total = total_movimientos

    @property
    def tipo(self) -> str:
        return "demo_inicio"

    def _datos_extra(self) -> dict:
        return {**super()._datos_extra(), "total_movimientos": self.__total}


class EventoDemoMovimiento(EventoDemo):
    def __init__(self, vehiculo_id: int, demo_id: int, comando_id: int, codigo,
                 orden: int, duracion_ms: int, pausa_ms: int):
        super().__init__(vehiculo_id, demo_id, comando_id, codigo)
        self.__orden = orden
        self.__duracion_ms = duracion_ms
        self.__pausa_ms = pausa_ms

    @property
    def tipo(self) -> str:
        return "demo_movimiento"

    def _datos_extra(self) -> dict:
        return {**super()._datos_extra(), "orden": self.__orden,
                "duracion_ms": self.__duracion_ms, "pausa_ms": self.__pausa_ms}


class EventoDemoFin(EventoDemo):
    @property
    def tipo(self) -> str:
        return "demo_fin"


class EventoDemoCancelada(EventoDemo):
    @property
    def tipo(self) -> str:
        return "demo_cancelada"

    def _datos_extra(self) -> dict:
        return {**super()._datos_extra(), "mensaje": "La DEMO fue cancelada por el usuario."}


class EventoDemoError(EventoDemo):
    @property
    def tipo(self) -> str:
        return "demo_error"

    def _datos_extra(self) -> dict:
        return {**super()._datos_extra(), "error": "Error interno durante la DEMO."}
