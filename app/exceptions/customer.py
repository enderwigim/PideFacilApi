from app.exceptions.base import AppException

# Excepciones relacionadas con los clientes:


# CustomerNotFoundError: Se lanza cuando no se encuentra un cliente con la referencia proporcionada.
class CustomerNotFoundError(AppException):
    def __init__(self, referencia: str):
        super().__init__(
            code="CUSTOMER_NOT_FOUND",
            message="No existe el cliente indicado.",
            status_code=404,
            details={"referenciaCliente": referencia},
        )


# CustomerNotActiveError: Se lanza cuando se intenta realizar una operación con un cliente que no está activo.
class CustomerNotActiveError(AppException):
    def __init__(self, referencia: str):
        super().__init__(
            code="CUSTOMER_NOT_ACTIVE",
            message="El cliente indicado no está activo.",
            status_code=400,
            details={"referenciaCliente": referencia},
        )
