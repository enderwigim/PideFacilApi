from typing import Any

from pydantic import BaseModel


class ErrorDetailSchema(BaseModel):
    code: str
    message: str
    details: Any = None


class ErrorResponseSchema(BaseModel):
    error: ErrorDetailSchema
