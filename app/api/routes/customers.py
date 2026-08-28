from fastapi import APIRouter

from app.db.session import DbSession
from app.schemas.customers.responses import CustomerSchema
from app.services.read_service import get_customers

router = APIRouter(
    prefix="/customers",
    tags=["Customers"],
)


@router.get("", response_model=list[CustomerSchema])
def read_customers(db: DbSession):
    return get_customers(db)
