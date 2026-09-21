from datetime import datetime

from fastapi import APIRouter, HTTPException

from app.api.v1.routes.documentation.responses import ORDER_RESPONSES
from app.api.v1.schemas.orders.requests import OrderCreationSchema
from app.api.v1.schemas.orders.responses import (
    OrderCreationResponseSchema,
    OrderHistorySchema,
)
from app.db.session import DbSession, TenantDbContext
from app.services.orders.orders_creation import create_order
from app.services.orders.orders_history import get_orderHistory

router = APIRouter(
    prefix="/order",
    tags=["Orders"],
)


@router.post(
    "",
    response_model=OrderCreationResponseSchema,
    status_code=201,
    summary="Crear pedido",
    response_description="Pedido creado correctamente.",
    responses=ORDER_RESPONSES,
)
def create_new_order(
    order: OrderCreationSchema,
    db: DbSession,
    context: TenantDbContext,
):
    return create_order(db=db, order=order, models=context.models)


@router.get("/history", response_model=list[OrderHistorySchema])
def read_orderHistory(
    db: DbSession,
    fromDate: datetime,
    UpToDate: datetime,
    context: TenantDbContext,
    customer: int | None = None,
):
    try:
        return get_orderHistory(
            db=db,
            fromDate=fromDate,
            UpToDate=UpToDate,
            customer=customer,
            models=context.models,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc
