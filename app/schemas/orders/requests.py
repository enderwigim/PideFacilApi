from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class DiscountSchema(BaseModel):
    dto1: Decimal | None = None
    dto2: Decimal | None = None
    dto3: Decimal | None = None
    dtoUM: Decimal | None = None


class CreationLineSchema(BaseModel):
    referenciaProducto: str
    cantidad: Decimal
    formatoDeVenta: str | None = None
    combination: int = 0
    peso_pieza: Decimal | None = None
    discounts: DiscountSchema | None = None


class OrderCreationSchema(BaseModel):
    referenciaCliente: str
    observaciones: str
    fechaEntrega: date | None = None
    sucursal: int | None = None
    lineas: list[CreationLineSchema]
