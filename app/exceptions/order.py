# Errores relacionados con la creación del pedido.
from app.exceptions.base import AppException


class CompanyNotFoundError(AppException):
    def __init__(self, referencia: str):
        super().__init__(
            code="COMPANY_NOT_FOUND",
            message="No existe la configuración de empresa.",
            status_code=404,
            details={"referenciaEmpresa": referencia},
        )


class UomNotFoundError(AppException):
    def __init__(self, referencia: str):
        super().__init__(
            code="UOM_NOT_FOUND",
            message="No existe la unidad de medida indicada.",
            status_code=404,
            details={"referenciaUnidadMedida": referencia},
        )


class PricesAndCostNotFound(AppException):
    def __init__(self, referencia: str):
        super().__init__(
            code="PRICES_AND_COST_NOT_FOUND",
            message="No existen precios ni costes para el artículo indicado.",
            status_code=409,
            details={"referenciaArticulo": referencia},
        )
