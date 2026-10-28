from models.entidades import Comando
from repositories.base_repository import RepositorioCRUD


class ComandoRepository(RepositorioCRUD):
    @property
    def entidad(self) -> str:
        return "comando"

    def construir(self, fila: dict) -> Comando:
        return Comando(fila)

    def obtener_por_vehiculo(self, vehiculo_id: int) -> list[Comando]:
        """sp_obtener_comandos_vehiculo"""
        return self._listar("sp_obtener_comandos_vehiculo", (vehiculo_id,))

    def crear(self, vehiculo_id: int, nombre: str, codigo: int, descripcion: str):
        """sp_crear_comando"""
        return self._escribir("sp_crear_comando", (vehiculo_id, nombre, codigo, descripcion), devolver=True)

    def actualizar(self, comando_id: int, nombre: str, codigo: int, descripcion: str, activo: bool):
        """sp_actualizar_comando"""
        self._escribir("sp_actualizar_comando", (comando_id, nombre, codigo, descripcion, activo))
        return {"mensaje": "Comando actualizado exitosamente"}

    def eliminar(self, identificador: int) -> dict:
        """sp_eliminar_comando"""
        self._escribir("sp_eliminar_comando", (identificador,))
        return {"mensaje": "Comando eliminado exitosamente"}
