import logging
from abc import ABC, abstractmethod
from typing import List, Optional

from config.database import DatabaseConnection
from models.entidad import Entidad

logger = logging.getLogger(__name__)


class BaseRepository(ABC):
    """Clase abstracta base de todos los repositorios.

    - ABSTRACCIÓN: oculta la conexión y los CALL a Stored Procedures.
    - ENCAPSULAMIENTO: la conexión es privada; solo las subclases usan los
      métodos protegidos `_consultar`, `_escribir`, `_listar`, `_obtener`.
    - POLIMORFISMO: `construir` es abstracto; cada repositorio devuelve su propio
      tipo de entidad y el resto del código lo trata como `Entidad`.
    """

    def __init__(self, db: DatabaseConnection):
        self.__db = db

    @property
    @abstractmethod
    def entidad(self) -> str:
        """Nombre de la entidad que gestiona el repositorio."""

    @abstractmethod
    def construir(self, fila: dict) -> Entidad:
        """Convierte una fila de la BD en el objeto de dominio correspondiente."""

    @staticmethod
    def _llamada(sp: str, params: tuple) -> str:
        return f"CALL {sp}({', '.join(['%s'] * len(params))})"

    def _consultar(self, sp: str, params: tuple = (), uno: bool = False):
        conexion = self.__db.obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                cursor.execute(self._llamada(sp, params), params)
                return cursor.fetchone() if uno else cursor.fetchall()
        finally:
            conexion.close()

    def _escribir(self, sp: str, params: tuple = (), devolver: bool = False):
        conexion = self.__db.obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                cursor.execute(self._llamada(sp, params), params)
                resultado = cursor.fetchone() if devolver else None
            conexion.commit()
            return resultado
        except Exception:
            conexion.rollback()
            logger.exception("Fallo al ejecutar %s (%s)", sp, self.entidad)
            raise
        finally:
            conexion.close()

    def _transaccion(self, llamadas: list[tuple[str, tuple]]) -> None:
        """Ejecuta varios SP en UNA sola transacción."""
        conexion = self.__db.obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                for sp, params in llamadas:
                    cursor.execute(self._llamada(sp, params), params)
                    while cursor.nextset():
                        pass
            conexion.commit()
        except Exception:
            conexion.rollback()
            raise
        finally:
            conexion.close()

    def _listar(self, sp: str, params: tuple = ()) -> List[Entidad]:
        return [self.construir(f) for f in self._consultar(sp, params) or []]

    def _obtener(self, sp: str, params: tuple = ()) -> Optional[Entidad]:
        fila = self._consultar(sp, params, uno=True)
        return self.construir(fila) if fila else None


class RepositorioCRUD(BaseRepository, ABC):
    """Segundo nivel de la jerarquía (herencia multinivel).

    Obliga a todo repositorio con ciclo de vida completo a implementar `eliminar`.
    """

    @abstractmethod
    def eliminar(self, identificador: int) -> dict:
        """Elimina la entidad (cada repositorio llama a su propio SP)."""
