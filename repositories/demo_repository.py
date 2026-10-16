from repositories.base_repository import BaseRepository


class DemoRepository(BaseRepository):
    """Gestiona las DEMO y sus movimientos."""

    def obtener_demos_vehiculo(self, vehiculo_id: int):
        """sp_obtener_demos"""
        return self._consultar("sp_obtener_demos", (vehiculo_id,))

    def obtener_movimientos_demo(self, demo_id: int):
        """sp_obtener_movimientos_demo (secuencia de N movimientos)"""
        return self._consultar("sp_obtener_movimientos_demo", (demo_id,))

    def crear_demo(self, vehiculo_id: int, nombre: str, descripcion: str):
        """sp_crear_demo"""
        return self._escribir("sp_crear_demo", (vehiculo_id, nombre, descripcion), devolver=True)

    def actualizar_demo(self, demo_id: int, nombre: str, descripcion: str, activo: bool):
        """sp_actualizar_demo"""
        self._escribir("sp_actualizar_demo", (demo_id, nombre, descripcion, activo))
        return {"mensaje": "Demo actualizada exitosamente"}

    def eliminar_demo(self, demo_id: int):
        """sp_eliminar_demo"""
        self._escribir("sp_eliminar_demo", (demo_id,))
        return {"mensaje": "Demo eliminada exitosamente"}

    def agregar_movimiento_demo(self, demo_id: int, comando_id: int, orden: int, duracion_ms: int, pausa_ms: int):
        """sp_agregar_movimiento_demo"""
        self._escribir(
            "sp_agregar_movimiento_demo", (demo_id, comando_id, orden, duracion_ms, pausa_ms)
        )
        return {"mensaje": "Movimiento de DEMO agregado exitosamente"}

    def actualizar_movimiento_demo(self, movimiento_id: int, comando_id: int, orden: int, duracion_ms: int, pausa_ms: int):
        """sp_actualizar_movimiento_demo"""
        self._escribir(
            "sp_actualizar_movimiento_demo", (movimiento_id, comando_id, orden, duracion_ms, pausa_ms)
        )
        return {"mensaje": "Movimiento de DEMO actualizado exitosamente"}

    def eliminar_movimiento_demo(self, movimiento_id: int):
        """sp_eliminar_movimiento_demo"""
        self._escribir("sp_eliminar_movimiento_demo", (movimiento_id,))
        return {"mensaje": "Movimiento de DEMO eliminado exitosamente"}
