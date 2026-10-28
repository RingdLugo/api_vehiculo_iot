from abc import ABC, abstractmethod
from typing import Any


class Entidad(ABC):
    """CLASE ABSTRACTA base de todos los objetos de dominio.

    - ABSTRACCIÓN: define QUÉ debe saber hacer toda entidad (`describir`,
      `_claves_id`) sin decir CÓMO; no se puede instanciar directamente.
    - ENCAPSULAMIENTO: los datos viven en un atributo privado (`__datos`);
      desde fuera solo se accede con métodos y propiedades.
    """

    def __init__(self, datos: dict):
        self.__datos = dict(datos or {})        # atributo privado (name mangling)

    # ---- métodos abstractos: cada subclase los implementa a su manera ----
    @property
    @abstractmethod
    def _claves_id(self) -> tuple:
        """Nombres de columna posibles para el identificador de la entidad."""

    @abstractmethod
    def describir(self) -> str:
        """Texto legible de la entidad (POLIMORFISMO: cada clase lo redefine)."""

    # ---- métodos de instancia comunes (HERENCIA: las subclases los reutilizan) ----
    def obtener(self, clave: str, defecto: Any = None) -> Any:
        """Lectura controlada de un dato interno."""
        valor = self.__datos.get(clave)
        return defecto if valor is None else valor

    @property
    def id(self):
        for clave in self._claves_id:
            valor = self.__datos.get(clave)
            if valor is not None:
                return valor
        return None

    def esta_activo(self) -> bool:
        return bool(self.obtener("activo", True))

    def a_diccionario(self) -> dict:
        """Copia de los datos (el diccionario interno nunca se expone)."""
        return dict(self.__datos)

    def __str__(self) -> str:
        return self.describir()

    def __repr__(self) -> str:
        return f"<{type(self).__name__} id={self.id}>"
