from datetime import datetime

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.db.models import (
    dli,
    dof,
    doh,
    uom,
)
from app.schemas.orders.responses import OrderHistorySchema


def get_orderHistory(
    db: Session, fromDate: datetime, UpToDate: datetime, customer: int | None = None
) -> list[OrderHistorySchema]:

    if fromDate > UpToDate:
        raise ValueError("fromDate cannot be greater than UpToDate")
    order_history = (
        db.query(doh, dli, uom)
        .join(dli, dli.doh_dli_fk == doh.doh_id)
        .outerjoin(uom, dli.uom_dli_fk == uom.uom_id)
        .outerjoin(
            dof,
            dof.dof_doclinedestiny == dli.dli_id,
        )
        .filter(
            # Aquí deberá ser un pedido o un albarán que no contenga un origen en un pedido.
            or_(
                doh.doh_type == 2,
                and_(
                    doh.doh_type == 3,
                    or_(
                        dof.dof_origintype.is_(None),
                        dof.dof_origintype != 2,
                    ),
                ),
            ),
            doh.doh_date >= fromDate,
            doh.doh_date <= UpToDate,
        )
        .order_by(doh.doh_date.asc())
    )
    if customer is not None:
        order_history = order_history.filter(doh.cus_doh_fk == customer)

    rows = order_history.all()

    result: list[OrderHistorySchema] = []
    for doh_data, dli_data, uom_data in rows:

        result.append(
            OrderHistorySchema(
                referenciaCliente=str(doh_data.cus_doh_fk),
                fechaCreacion=doh_data.doh_date,
                referenciaProducto=str(dli_data.ite_dli_fk),
                cantidad=dli_data.dli_quantity,
                formatoDeVenta=(
                    str(uom_data.uom_symbol) if uom_data is not None else None
                ),
            )
        )

    return result
