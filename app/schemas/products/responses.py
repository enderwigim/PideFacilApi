from pydantic import BaseModel, Field


class ProductFormatSchema(BaseModel):
    referenciaFormato: str
    nombre: str
    unidadesPorFormato: float


class DimFormatSchema(BaseModel):
    referencia: str
    nombre: str


# Empezaré a montar los schemas con una estructura que nos sea familiar. No como ellos piden.
class IdcFormatSchema(BaseModel):
    idc_id: int
    idc_dim_one: int = 0
    idc_dim_one_value: str | None = None
    idc_dim_two: int = 0
    idc_dim_two_value: str | None = None


# 2026-08-25 De inicio agregamos los campos básicos que debe devolver el esquema.
class ProductSchema(BaseModel):
    referencia: str
    nombre: str
    formatosDeVenta: list[ProductFormatSchema] = Field(default_factory=list)
    combinations: list[IdcFormatSchema] = Field(default_factory=list)
    # dim_one: list[DimFormatSchema] = Field(default_factory=list)
    # dim_two: list[DimFormatSchema] = Field(default_factory=list)
