from datetime import datetime

from fastapi import APIRouter

from app.db.session import DbSession
from app.schemas.order_history import OrderHistorySchema
from app.services.read_service import get_orderHistory

router = APIRouter(
    prefix="/orderHistory",
    tags=["Customers"],
)


@router.get("", response_model=list[OrderHistorySchema])
def read_orderHistory(
    db: DbSession,
    fromDate: datetime,
    UpToDate: datetime,
    customer: str | None = None,
):
    return get_orderHistory(
        db=db,
        fromDate=fromDate,
        UpToDate=UpToDate,
        customer=customer,
    )
