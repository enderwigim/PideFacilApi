# app/schemas/order_history.py

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.api.v1.schemas.products.responses import IdcFormatSchema

# class OrderHistorySchema(BaseModel):
#     referenciaCliente: str
#     fechaCreacion: datetime
#     referenciaProducto: str
#     cantidad: Decimal | None = None
#     formatoDeVenta: str | None = None


class OrderHistorySchema(BaseModel):
    referenciaCliente: str = Field(
        description="Referencia del cliente en IntegraQS.",
        examples=["12"],
    )
    fechaCreacion: datetime = Field(
        description="Fecha de creación del pedido.",
        examples=["2024-06-01T12:34:56"],
    )
    referenciaProducto: str = Field(
        description="Referencia del producto en IntegraQS.",
        examples=["B12"],
    )
    cantidad: Decimal | None = Field(
        default=None,
        description="Cantidad del producto en el pedido.",
        examples=[3.5],
    )
    formatoDeVenta: str | None = (
        Field(
            default=None,
            description="Referencia del formato de venta utilizado.",
            examples=["C6"],
        ),
    )
    combination: IdcFormatSchema | None = Field(
        default=None,
        description="Combinación del artículo en esquema [IdcFormatSchema]",
    )


class OrderCreationResponseSchema(BaseModel):
    orderId: int = Field(description="Referencia interna del pedido en IntegraQS")
    seqnumber: str = Field(
        description="Serie y número del documento creado en IntegraQS"
    )
