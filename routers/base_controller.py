from abc import ABC, abstractmethod

from fastapi import APIRouter, FastAPI

from models.entidad import Entidad


class BaseController(ABC):

    def __init__(self, prefix: str, tags: list[str]):
        self._router = APIRouter(prefix=prefix, tags=tags)
        self._registrar_rutas()

    @abstractmethod
    def _registrar_rutas(self) -> None:
        """Declara los endpoints del controlador."""

    def registrar(self, app: FastAPI) -> None:
        app.include_router(self._router)

    def _ruta(self, path: str, endpoint, metodo: str, summary: str, description: str = "", **opciones):
        self._router.add_api_route(
            path, endpoint, methods=[metodo], summary=summary, description=description, **opciones
        )

    @staticmethod
    def _serializar(obj):
        """Convierte entidades (o listas de entidades) a diccionarios para JSON."""
        if isinstance(obj, Entidad):
            return obj.a_diccionario()
        if isinstance(obj, list):
            return [BaseController._serializar(o) for o in obj]
        return obj
