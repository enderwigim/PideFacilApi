from fastapi import APIRouter

from app.api.v1.schemas.customers.responses import CustomerSchema
from app.db.session import DbSession, TenantDbContext
from app.services.customers import get_customer_by_id, get_customers

router = APIRouter(
    prefix="/customers",
    tags=["Customers"],
)


@router.get("", response_model=list[CustomerSchema])
def read_customers(db: DbSession, context: TenantDbContext):
    return get_customers(db, models=context.models)


@router.get("/{cus_id}", response_model=CustomerSchema)
def read_customer_by_id(db: DbSession, n_cus_id, context: TenantDbContext):
    return get_customer_by_id(db, n_cus_id, models=context.models)
