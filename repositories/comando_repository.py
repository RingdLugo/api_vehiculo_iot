from repositories.base_repository import BaseRepository


class ComandoRepository(BaseRepository):
    """Gestiona los comandos asociados a los vehículos."""

    def obtener_por_vehiculo(self, vehiculo_id: int):
        """sp_obtener_comandos_vehiculo"""
        return self._consultar("sp_obtener_comandos_vehiculo", (vehiculo_id,))

    def crear(self, vehiculo_id: int, nombre: str, codigo: str, descripcion: str):
        """sp_crear_comando"""
        return self._escribir(
            "sp_crear_comando", (vehiculo_id, nombre, codigo, descripcion), devolver=True
        )

    def actualizar(self, comando_id: int, nombre: str, codigo: str, descripcion: str, activo: bool):
        """sp_actualizar_comando"""
        self._escribir("sp_actualizar_comando", (comando_id, nombre, codigo, descripcion, activo))
        return {"mensaje": "Comando actualizado exitosamente"}

    def eliminar(self, comando_id: int):
        """sp_eliminar_comando"""
        self._escribir("sp_eliminar_comando", (comando_id,))
        return {"mensaje": "Comando eliminado exitosamente"}
