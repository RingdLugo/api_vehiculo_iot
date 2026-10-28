import logging
import os

import pymysql
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from core.contenedor import Contenedor
from routers.base_controller import BaseController
from routers.comando_router import ComandoController
from routers.demo_router import DemoController
from routers.vehiculo_router import VehiculoController
from routers.ws_router import WebSocketController

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("api_vehiculo_iot")


class AplicacionAPI:
    """Construye y configura la aplicación FastAPI."""

    def __init__(self, contenedor: Contenedor | None = None):
        self._c = contenedor or Contenedor()
        self.app = FastAPI(
            title="API Vehículo IoT",
            description=("API desarrollada con FastAPI, Programación Orientada a Objetos, Amazon RDS "
                         "(Stored Procedures) y WebSockets para la gestión de vehículos IoT."),
            version="1.0.0",
        )
        self._configurar_cors()
        self._registrar_controladores()
        self._registrar_manejadores_errores()
        self.app.add_api_route("/", self.root, methods=["GET"], tags=["General"])

    def _configurar_cors(self) -> None:
        origenes = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",") if o.strip()]
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=origenes,
            allow_credentials=origenes != ["*"],
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def _registrar_controladores(self) -> None:
        c = self._c
        controladores: list[BaseController] = [
            VehiculoController(c.vehiculo_repo, c.comando_repo, c.estado_repo, c.demo_repo,
                               c.operacion_service),
            ComandoController(c.comando_repo, c.manager),
            DemoController(c.demo_repo, c.manager),
            WebSocketController(c.vehiculo_repo, c.manager),
        ]
        for controlador in controladores:      # polimorfismo: todos responden a registrar()
            controlador.registrar(self.app)

    def _registrar_manejadores_errores(self) -> None:
        self.app.add_exception_handler(pymysql.err.IntegrityError, self._integridad_handler)
        self.app.add_exception_handler(pymysql.MySQLError, self._mysql_handler)

    @staticmethod
    async def _integridad_handler(request: Request, exc: pymysql.err.IntegrityError):
        return JSONResponse(status_code=409, content={
            "detail": "La operación viola una restricción de la base de datos "
                      "(dato duplicado o referencia inválida)."})

    @staticmethod
    async def _mysql_handler(request: Request, exc: pymysql.MySQLError):
        codigo = exc.args[0] if exc.args and isinstance(exc.args[0], int) else None
        if codigo == 1644 and len(exc.args) > 1:
            return JSONResponse(status_code=400, content={"detail": str(exc.args[1])})
        logger.error("Error de base de datos: %s", exc)
        return JSONResponse(status_code=500,
                            content={"detail": "Error interno en el servidor de base de datos."})

    @staticmethod
    def root():
        return {
            "mensaje": "Servidor FastAPI para Vehículo IoT operando correctamente en entorno Dev",
            "documentacion": "/docs",
            "websocket_endpoint": "/ws/vehiculo/{vehiculo_id}",
        }


app = AplicacionAPI().app
