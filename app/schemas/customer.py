from pydantic import BaseModel


class CustomerSchema(BaseModel):
    referencia: str
    nombre: str
    telefonos: list[str]
    referenciaComercial: str | None = None
