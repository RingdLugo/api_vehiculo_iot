from config.database import DatabaseConnection


def extraer_id(fila: dict, *claves: str):
    """Devuelve el primer valor existente entre las claves indicadas.

    Permite tolerar nombres de columna distintos devueltos por los SP
    (por ejemplo "id" o "id_comando").
    """
    for clave in claves:
        if fila.get(clave) is not None:
            return fila[clave]
    return None


class BaseRepository:
    """Clase base: centraliza el patrón abrir conexión -> CALL sp -> cerrar."""

    def __init__(self):
        self.db = DatabaseConnection()

    def _consultar(self, sp: str, params: tuple = (), uno: bool = False):
        """Ejecuta un SP de lectura y devuelve una fila (uno=True) o todas."""
        conexion = self.db.obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                cursor.execute(self._llamada(sp, params), params)
                return cursor.fetchone() if uno else cursor.fetchall()
        finally:
            conexion.close()

    def _escribir(self, sp: str, params: tuple = (), devolver: bool = False):
        """Ejecuta un SP de escritura dentro de una transacción."""
        conexion = self.db.obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                cursor.execute(self._llamada(sp, params), params)
                resultado = cursor.fetchone() if devolver else None
            conexion.commit()
            return resultado
        except Exception:
            conexion.rollback()
            raise
        finally:
            conexion.close()

    @staticmethod
    def _llamada(sp: str, params: tuple) -> str:
        marcadores = ", ".join(["%s"] * len(params))
        return f"CALL {sp}({marcadores})"
