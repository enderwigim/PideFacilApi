from app.exceptions.base import AppException


class ApiKeyRequired(AppException):
    def __init__(self):
        super().__init__(
            code="API_KEY_REQUIRED",
            message="No se ha enviado la API Key",
            status_code=401,
        )


class ApiKeyInvalidFormat(AppException):
    def __init__(self):
        super().__init__(
            code="API_KEY_INVALID_FORMAT",
            message="El formato de la API Key no es correcto.",
            status_code=401,
        )


class ApiKeyNotFound(AppException):
    def __init__(self):
        super().__init__(
            code="API_KEY_NOT_FOUND",
            message="La API Key proporcionada no es válida.",
            status_code=401,
        )


class ApiKeyDisabled(AppException):
    def __init__(self):
        super().__init__(
            code="API_KEY_DISABLED",
            message="La API Key se encuentra deshabilitada.",
            status_code=401,
        )


class ApiKeyExpired(AppException):
    def __init__(self):
        super().__init__(
            code="API_KEY_EXPIRED",
            message="La API Key ha caducado.",
            status_code=401,
        )


class ApiKeyTenantMismatch(AppException):
    def __init__(self):
        super().__init__(
            code="API_KEY_TENANT_MISMATCH",
            message="La API Key no está autorizada para este Tenant.",
            status_code=401,
        )
