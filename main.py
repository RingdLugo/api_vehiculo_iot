import logging
import os

import pymysql
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from routers import comando_router, demo_router, vehiculo_router, ws_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("api_vehiculo_iot")

app = FastAPI(
    title="API Vehículo IoT",
    description=("API desarrollada con FastAPI, Programación Orientada a Objetos, Amazon RDS "
                 "(Stored Procedures) y WebSockets para la gestión de vehículos IoT."),
    version="1.0.0",
)

origenes = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origenes,
    allow_credentials=origenes != ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(vehiculo_router.router)
app.include_router(comando_router.router)
app.include_router(demo_router.router)
app.include_router(ws_router.router)


@app.exception_handler(pymysql.err.IntegrityError)
async def integridad_handler(request: Request, exc: pymysql.err.IntegrityError):
    return JSONResponse(status_code=409, content={
        "detail": "La operación viola una restricción de la base de datos (dato duplicado o referencia inválida)."})


@app.exception_handler(pymysql.MySQLError)
async def mysql_handler(request: Request, exc: pymysql.MySQLError):
    codigo = exc.args[0] if exc.args and isinstance(exc.args[0], int) else None
    if codigo == 1644 and len(exc.args) > 1:
        return JSONResponse(status_code=400, content={"detail": str(exc.args[1])})
    logger.error("Error de base de datos: %s", exc)
    return JSONResponse(status_code=500, content={"detail": "Error interno en el servidor de base de datos."})


@app.get("/", tags=["General"])
def root():
    return {
        "mensaje": "Servidor FastAPI para Vehículo IoT operando correctamente en entorno Dev",
        "documentacion": "/docs",
        "websocket_endpoint": "/ws/vehiculo/{vehiculo_id}",
    }