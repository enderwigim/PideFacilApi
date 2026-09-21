from pydantic import BaseModel


class AgentSchema(BaseModel):
    age_id: str
    age_name: str
    age_phone: str | None = None
