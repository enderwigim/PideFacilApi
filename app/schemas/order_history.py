# app/schemas/order_history.py

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class OrderHistorySchema(BaseModel):
    referenciaCliente: str
    fechaCreacion: datetime
    referenciaProducto: str
    cantidad: Decimal | None = None
    formatoDeVenta: str | None = None
