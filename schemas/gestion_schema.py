from pydantic import BaseModel, Field


class VehiculoCrear(BaseModel):
    nombre: str = Field(..., min_length=1, example="Excavadora 01")
    descripcion: str = Field("", example="Excavadora a escala controlada por ESP32")


class VehiculoActualizar(VehiculoCrear):
    activo: bool = True


class ComandoCrear(BaseModel):
    vehiculo_id: int = Field(..., example=1)
    nombre: str = Field(..., min_length=1, example="Avanzar")
    codigo: int = Field(..., description="Código numérico del comando (único por vehículo).", example=1)
    descripcion: str = Field("", example="Mueve el vehículo hacia adelante")


class ComandoActualizar(BaseModel):
    nombre: str = Field(..., min_length=1)
    codigo: int = Field(..., description="Código numérico del comando (único por vehículo).")
    descripcion: str = ""
    activo: bool = True


class DemoCrear(BaseModel):
    vehiculo_id: int = Field(..., example=1)
    nombre: str = Field(..., min_length=1, example="Demo de bienvenida")
    descripcion: str = Field("", example="Secuencia de ejemplo")


class DemoActualizar(BaseModel):
    nombre: str = Field(..., min_length=1)
    descripcion: str = ""
    activo: bool = True


class MovimientoDemoCrear(BaseModel):
    comando_id: int = Field(..., example=1)
    orden: int = Field(..., ge=1, example=1)
    duracion_ms: int = Field(1000, ge=0, example=1000)
    pausa_ms: int = Field(500, ge=0, example=500)


class MovimientoDemoActualizar(MovimientoDemoCrear):
    pass