from app.exceptions.base import AppException

# Excepciones relacionadas con los agentes commerciales:


# CommercialAgentNotFound: Se lanza cuando no se encuentra un cliente con la referencia proporcionada.
class CommercialAgentNotFound(AppException):
    def __init__(self, referencia: str):
        super().__init__(
            code="COMMERCIAL_AGENT_NOT_FOUND",
            message="No se ha encontrado ningún agente.",
            status_code=404,
            # details={"referenciaCliente": referencia},
        )
