from fastapi import APIRouter

from app.db.session import DbSession
from app.schemas.order_creation import OrderCreationSchema
from app.services.write_service import create_order

router = APIRouter(
    prefix="/order",
    tags=["Orders"],
)


@router.post("")
def create_new_order(
    order: OrderCreationSchema,
    db: DbSession,
):
    return create_order(
        db=db,
        order=order,
    )
