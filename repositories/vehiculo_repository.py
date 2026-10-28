from models.entidades import Vehiculo
from repositories.base_repository import RepositorioCRUD


class VehiculoRepository(RepositorioCRUD):
    @property
    def entidad(self) -> str:
        return "vehiculo"

    def construir(self, fila: dict) -> Vehiculo:
        return Vehiculo(fila)

    def obtener_todos(self) -> list[Vehiculo]:
        """sp_obtener_vehiculos"""
        return self._listar("sp_obtener_vehiculos")

    def obtener_por_id(self, vehiculo_id: int):
        """sp_obtener_vehiculo"""
        return self._obtener("sp_obtener_vehiculo", (vehiculo_id,))

    def crear(self, nombre: str, descripcion: str):
        """sp_crear_vehiculo"""
        return self._escribir("sp_crear_vehiculo", (nombre, descripcion), devolver=True)

    def actualizar(self, vehiculo_id: int, nombre: str, descripcion: str, activo: bool):
        """sp_actualizar_vehiculo"""
        self._escribir("sp_actualizar_vehiculo", (vehiculo_id, nombre, descripcion, activo))
        return {"mensaje": "Vehículo actualizado exitosamente"}

    def eliminar(self, identificador: int) -> dict:
        """sp_eliminar_vehiculo"""
        self._escribir("sp_eliminar_vehiculo", (identificador,))
        return {"mensaje": "Vehículo eliminado exitosamente"}
