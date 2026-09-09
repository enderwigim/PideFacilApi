# Las excepciones personalizadas de la aplicación mantendrán esta estructura base,
# manteniendo la consistencia.

# Estructura
# {
#   "error": {
#     "code": "CODIGO_DE_ERROR",
#     "message": "Mensaje de error",
#     "details": {}
#   }
# }


class AppException(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        details: dict | None = None,
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
