from config.database import DatabaseConnection
from repositories.base_repository import RepositorioCRUD
from repositories.comando_repository import ComandoRepository
from repositories.demo_repository import DemoRepository
from repositories.estado_historial_repository import EstadoHistorialRepository
from repositories.vehiculo_repository import VehiculoRepository
from services.operacion_service import OperacionService
from ws_manager.manager import ConnectionManager


class Contenedor:
    """Raíz de composición: crea UNA vez cada objeto y le inyecta sus dependencias."""

    def __init__(self):
        self.db = DatabaseConnection()

        self.vehiculo_repo = VehiculoRepository(self.db)
        self.comando_repo = ComandoRepository(self.db)
        self.demo_repo = DemoRepository(self.db)
        self.estado_repo = EstadoHistorialRepository(self.db)

        self.manager = ConnectionManager(self.estado_repo)
        self.operacion_service = OperacionService(
            vehiculo_repo=self.vehiculo_repo,
            comando_repo=self.comando_repo,
            demo_repo=self.demo_repo,
            estado_repo=self.estado_repo,
            manager=self.manager,
        )

    def repositorios_crud(self) -> list[RepositorioCRUD]:
        return [self.vehiculo_repo, self.comando_repo, self.demo_repo]
