from repositories.base_repository import BaseRepository


class VehiculoRepository(BaseRepository):
    """Gestiona los vehículos mediante Stored Procedures."""

    def obtener_todos(self):
        """sp_obtener_vehiculos"""
        return self._consultar("sp_obtener_vehiculos")

    def obtener_por_id(self, vehiculo_id: int):
        """sp_obtener_vehiculo"""
        return self._consultar("sp_obtener_vehiculo", (vehiculo_id,), uno=True)

    def crear(self, nombre: str, descripcion: str):
        """sp_crear_vehiculo"""
        return self._escribir("sp_crear_vehiculo", (nombre, descripcion), devolver=True)

    def actualizar(self, vehiculo_id: int, nombre: str, descripcion: str, activo: bool):
        """sp_actualizar_vehiculo"""
        self._escribir("sp_actualizar_vehiculo", (vehiculo_id, nombre, descripcion, activo))
        return {"mensaje": "Vehículo actualizado exitosamente"}

    def eliminar(self, vehiculo_id: int):
        """sp_eliminar_vehiculo"""
        self._escribir("sp_eliminar_vehiculo", (vehiculo_id,))
        return {"mensaje": "Vehículo eliminado exitosamente"}
