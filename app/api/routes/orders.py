from datetime import datetime

from fastapi import APIRouter, HTTPException

from app.db.session import DbSession
from app.schemas.orders.requests import OrderCreationSchema
from app.schemas.orders.responses import OrderHistorySchema
from app.services.orders.orders_creation import create_order
from app.services.read_service import get_orderHistory

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


@router.get("/history", response_model=list[OrderHistorySchema])
def read_orderHistory(
    db: DbSession,
    fromDate: datetime,
    UpToDate: datetime,
    customer: int | None = None,
):
    try:
        return get_orderHistory(
            db=db,
            fromDate=fromDate,
            UpToDate=UpToDate,
            customer=customer,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc
