# Errores relacionados con los productos.
from app.exceptions.base import AppException


class ProductNotFoundError(AppException):
    def __init__(self, referencia: str):
        super().__init__(
            code="PRODUCT_NOT_FOUND",
            message="No existe el producto indicado.",
            status_code=404,
            details={"referenciaProducto": referencia},
        )


class CombinationNotFoundError(AppException):
    def __init__(self, referencia: str):
        super().__init__(
            code="COMBINATION_NOT_FOUND",
            message="No existe la combinación de producto indicada.",
            status_code=404,
            details={"referenciaCombinacion": referencia},
        )


class UomProductNotFoundError(AppException):
    def __init__(self, referencia: str):
        super().__init__(
            code="UOM_PRODUCT_NOT_FOUND",
            message="No existe la unidad de medida indicada, para este artículo.",
            status_code=404,
            details={"referenciaUnidadMedida": referencia},
        )


class UomConversionError(AppException):
    def __init__(self, message: str, referencia: str):
        super().__init__(
            code="UOM_CONVERSION_ERROR",
            message=(
                message if message else "Error en la conversión de unidades de medida."
            ),
            status_code=400,
            details={"referenciaUnidadMedida": referencia},
        )
