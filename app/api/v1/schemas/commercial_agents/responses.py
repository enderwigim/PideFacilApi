from pydantic import BaseModel


class AgentSchema(BaseModel):
    referencia: str
    nombre: str
    telefono: str | None = None
