from config.database import DatabaseConnection


class ProbadorConexion:
    """Verifica la conexión con RDS."""

    def __init__(self, db: DatabaseConnection):
        self._db = db

    def ejecutar(self) -> bool:
        conexion = None
        try:
            conexion = self._db.obtener_conexion()
            with conexion.cursor() as cursor:
                cursor.execute("SELECT DATABASE() AS base_datos")
                resultado = cursor.fetchone()
            print("Conexión exitosa con RDS")
            print("Base de datos:", resultado["base_datos"])
            return True
        except Exception as error:
            print("No se pudo conectar con RDS")
            print("Error:", error)
            return False
        finally:
            if conexion is not None:
                conexion.close()


if __name__ == "__main__":
    ProbadorConexion(DatabaseConnection()).ejecutar()