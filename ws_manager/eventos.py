"""Eventos del WebSocket: nombres y estructura de los mensajes.

Todo mensaje que sale por el WebSocket tiene estos campos:
    tipo, vehiculo_id, comando_id, codigo, marca_temporal
Lo que no aplique a un evento viaja como null. Cada evento puede traer
campos extra (demo_id, orden, duracion_ms, etc.).
"""
import datetime

from fastapi.encoders import jsonable_encoder


class TipoEvento:
    """Nombres de los eventos que envía el servidor."""
    CONEXION_ESTABLECIDA = "conexion_establecida"
    MOVIMIENTO_INDIVIDUAL = "movimiento_individual"
    DEMO_INICIO = "demo_inicio"
    DEMO_MOVIMIENTO = "demo_movimiento"
    DEMO_FIN = "demo_fin"
    DEMO_CANCELADA = "demo_cancelada"
    DEMO_ERROR = "demo_error"
    PONG = "pong"


def marca_temporal() -> str:
    """Fecha y hora actual en formato ISO 8601."""
    return datetime.datetime.now().isoformat()


def construir_evento(tipo: str, vehiculo_id: int, **datos) -> dict:
    """Arma un evento con la estructura estándar y lo deja listo para JSON.

    jsonable_encoder convierte fechas (datetime) y decimales que vienen de
    la base de datos, que send_json no puede enviar directamente.
    """
    evento = {
        "tipo": tipo,
        "vehiculo_id": vehiculo_id,
        "comando_id": None,
        "codigo": None,
        "marca_temporal": marca_temporal(),
    }
    evento.update(datos)
    return jsonable_encoder(evento)
