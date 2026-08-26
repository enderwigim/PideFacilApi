from datetime import datetime

from fastapi import APIRouter, HTTPException

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
