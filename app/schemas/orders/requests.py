from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class CreationLineSchema(BaseModel):
    referenciaProducto: str
    cantidad: Decimal
    formatoDeVenta: str | None = None
    combination: int = 0
    peso_pieza: Decimal | None = None


class OrderCreationSchema(BaseModel):
    referenciaCliente: str
    observaciones: str
    fechaEntrega: date | None = None
    lineas: list[CreationLineSchema]
