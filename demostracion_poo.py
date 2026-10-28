"""Demostración en vivo de los 4 pilares de la POO. No necesita base de datos.

Ejecutar:  python demostracion_poo.py
"""
from config.database import DatabaseConnection
from models.entidad import Entidad
from models.entidades import Comando, Demo, MovimientoDemo, Vehiculo
from repositories.base_repository import BaseRepository, RepositorioCRUD
from repositories.comando_repository import ComandoRepository
from repositories.vehiculo_repository import VehiculoRepository
from ws_manager.eventos import (
    Evento, EventoDemo, EventoDemoInicio, EventoDemoMovimiento, EventoMovimientoIndividual,
)


def titulo(texto: str) -> None:
    print(f"\n=== {texto} ===")


titulo("1. CLASE y OBJETO (instancias con métodos de instancia)")
auto = Vehiculo({"id_vehiculo": 1, "nombre": "Excavadora 01", "activo": True})
paso = MovimientoDemo({"id_comando": 2, "orden": 1, "duracion_ms": 1500, "pausa_ms": 500})
print(auto.describir())
print("¿activo?:", auto.esta_activo())
print("espera total del paso:", paso.espera_total_segundos(), "s")

titulo("2. ABSTRACCIÓN (clases abstractas no se pueden instanciar)")
for clase in (Entidad, BaseRepository, RepositorioCRUD, Evento, EventoDemo):
    try:
        clase({}) if clase is Entidad else clase()
    except TypeError as e:
        print(f"{clase.__name__}: TypeError -> {str(e)[:70]}...")

titulo("3. HERENCIA (jerarquías)")
print("VehiculoRepository MRO:", [c.__name__ for c in VehiculoRepository.__mro__ if c is not object])
print("EventoDemoInicio MRO:  ", [c.__name__ for c in EventoDemoInicio.__mro__ if c is not object])

titulo("4. POLIMORFISMO (mismo método, comportamiento distinto)")
entidades: list[Entidad] = [
    auto,
    Comando({"id_comando": 5, "nombre": "Avanzar", "codigo": 1}),
    Demo({"id_demo": 3, "nombre": "Bienvenida"}),
    paso,
]
for e in entidades:                      # el ciclo no sabe qué clase es cada una
    print("describir() ->", e.describir())

eventos: list[Evento] = [
    EventoMovimientoIndividual(1, 5, 1, "WEB_API"),
    EventoDemoInicio(1, 3, 4),
    EventoDemoMovimiento(1, 3, 5, 1, 1, 1000, 500),
]
for ev in eventos:
    d = ev.a_diccionario()
    print(f"{ev.tipo:22s} extras ->", {k: v for k, v in d.items() if k not in
          ("tipo", "vehiculo_id", "comando_id", "codigo", "marca_temporal")})

db = DatabaseConnection()
for repo in (VehiculoRepository(db), ComandoRepository(db)):
    print(f"repo '{repo.entidad}' construye ->", type(repo.construir({"id": 1})).__name__)

titulo("5. ENCAPSULAMIENTO (datos privados, acceso controlado)")
try:
    print(auto.__datos)
except AttributeError as e:
    print("auto.__datos ->", e)
copia = auto.a_diccionario()
copia["nombre"] = "HACKEADO"
print("modificar la copia no afecta al objeto:", auto.nombre)
