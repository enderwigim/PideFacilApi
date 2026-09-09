from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field


class DiscountSchema(BaseModel):
    dto1: Decimal | None = Field(
        default=None,
        description="Porcentaje de descuento en cascada 1.",
        examples=[15.2],
    )
    dto2: Decimal | None = Field(
        default=None,
        description="Porcentaje de descuento en cascada 2.",
        examples=[15.2],
    )
    dto3: Decimal | None = Field(
        default=None,
        description="Porcentaje de descuento en cascada 2.",
        examples=[15.2],
    )
    dtoUM: Decimal | None = Field(
        default=None,
        description="Descuento en euros por unidad de línea.",
        examples=[15.2],
    )


# class CreationLineSchema(BaseModel):
#     referenciaProducto: str
#     cantidad: Decimal
#     formatoDeVenta: str | None = None
#     combination: int = 0
#     peso_pieza: Decimal | None = None
#     discounts: DiscountSchema | None = None
#     reserved: bool | None = False
#     notes: str | None = None


class CreationLineSchema(BaseModel):

    referenciaProducto: str = Field(
        description="Referencia del producto IntegraQS.",
        examples=["B12"],
    )

    cantidad: Decimal = Field(
        gt=0,
        description="Cantidad solicitada del producto.",
        examples=[3.5],
    )

    formatoDeVenta: str | None = Field(
        default=None,
        description=(
            "Referencia del formato de venta utilizado. "
            "Solo debe enviarse cuando el producto utilice formatos de venta."
        ),
        examples=["C6"],
    )

    combination: int = Field(
        default=0,
        description=(
            "Identificador de combinación del producto. "
            "Se utiliza únicamente en productos que gestionan combinaciones."
        ),
        examples=[4115],
    )

    peso_pieza: Decimal | None = Field(
        default=None,
        description="Peso por pieza cuando sea aplicable.",
        examples=[1.25],
    )


# class OrderCreationSchema(BaseModel):
#     referenciaCliente: str
#     observaciones: str | None = None
#     fechaEntrega: date | None = None
#     sucursal: int | None = None
#     almacen: int | None = None
#     lineas: list[CreationLineSchema]
class OrderCreationSchema(BaseModel):

    referenciaCliente: str = Field(
        description="Referencia del cliente en IntegraQS.",
        examples=["12"],
    )

    observaciones: str = Field(
        description="Observaciones introducidas por el cliente.",
        examples=["Dejar en recepción"],
    )

    fechaEntrega: date | None = Field(
        default=None,
        description=(
            "Fecha de entrega solicitada o calculada por PideFácil, "
            "en formato ISO 8601."
        ),
        examples=["2026-09-09"],
    )

    sucursal: int | None = Field(
        default=None,
        description="Sucursal en la que debe generarse el pedido.",
        examples=[0],
    )

    almacen: int | None = Field(
        default=None,
        description="Almacén asociado al pedido.",
        examples=[0],
    )

    lineas: list[CreationLineSchema] = Field(
        min_length=1,
        description="Líneas que componen el pedido.",
    )
