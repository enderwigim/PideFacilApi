from pydantic import BaseModel, Field


class ProductFormatSchema(BaseModel):
    referenciaFormato: str
    nombre: str
    unidadesPorFormato: float


# 2026-08-25 De inicio agregamos los campos básicos que debe devolver el esquema.
class ProductSchema(BaseModel):
    referencia: str
    nombre: str
    formatosDeVenta: list[ProductFormatSchema] = Field(default_factory=list)
