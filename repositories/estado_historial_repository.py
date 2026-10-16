from repositories.base_repository import BaseRepository

LIMITE_HISTORIAL = 10


class EstadoHistorialRepository(BaseRepository):
    """Gestiona el estado actual y el historial de movimientos individuales."""

    def obtener_estado(self, vehiculo_id: int):
        """sp_obtener_estado"""
        return self._consultar("sp_obtener_estado", (vehiculo_id,), uno=True)

    def actualizar_estado(self, vehiculo_id: int, comando_id: int, origen: str):
        """sp_actualizar_estado (lo usan movimientos individuales y DEMO)."""
        self._escribir("sp_actualizar_estado", (vehiculo_id, comando_id, origen))
        return True

    def registrar_historial(self, vehiculo_id: int, comando_id: int, origen: str):
        """sp_registrar_historial (exclusivo de movimientos individuales)."""
        self._escribir("sp_registrar_historial", (vehiculo_id, comando_id, origen))
        return True

    def registrar_movimiento_atomico(self, vehiculo_id: int, comando_id: int, origen: str):
        """Ejecuta sp_actualizar_estado + sp_registrar_historial en UNA sola
        transacción: o se guardan ambos o no se guarda ninguno."""
        conexion = self.db.obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                cursor.execute("CALL sp_actualizar_estado(%s, %s, %s)", (vehiculo_id, comando_id, origen))
                while cursor.nextset():
                    pass
                cursor.execute("CALL sp_registrar_historial(%s, %s, %s)", (vehiculo_id, comando_id, origen))
                while cursor.nextset():
                    pass
            conexion.commit()
            return True
        except Exception:
            conexion.rollback()
            raise
        finally:
            conexion.close()

    def obtener_historial_reciente(self, vehiculo_id: int):
        """sp_obtener_historial limitado a los 10 movimientos más recientes.

        Requiere que el SP ordene de más reciente a más antiguo
        (ORDER BY ... DESC). Ver README, sección "Historial".
        """
        resultado = self._consultar("sp_obtener_historial", (vehiculo_id,))
        return list(resultado[:LIMITE_HISTORIAL]) if resultado else []
