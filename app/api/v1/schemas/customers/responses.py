from pydantic import BaseModel


class CustomerSchema(BaseModel):
    cus_id: str
    cus_name: str
    cus_phones: list[str]
    age_cus: str | None = None
