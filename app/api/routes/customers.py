from fastapi import APIRouter

from app.db.session import DbSession
from app.schemas.customers.responses import CustomerSchema
from app.services.customers import get_customer_by_id, get_customers

router = APIRouter(
    prefix="/customers",
    tags=["Customers"],
)


@router.get("", response_model=list[CustomerSchema])
def read_customers(db: DbSession):
    return get_customers(db)


@router.get("/{cus_id}", response_model=CustomerSchema)
def read_customer_by_id(db: DbSession, n_cus_id):
    return get_customer_by_id(db, n_cus_id)
