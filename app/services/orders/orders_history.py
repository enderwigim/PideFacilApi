from datetime import datetime

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from app.db.models import (
    dli,
    dof,
    doh,
    uom,
)
from app.schemas.orders.responses import OrderHistorySchema
from app.schemas.products.responses import IdcFormatSchema


def get_orderHistory(
    db: Session, fromDate: datetime, UpToDate: datetime, customer: int | None = None
) -> list[OrderHistorySchema]:
    idc_schema: IdcFormatSchema | None = None
    if fromDate > UpToDate:
        raise ValueError("fromDate cannot be greater than UpToDate")
    order_history = (
        db.query(
            doh.doh_id.label("doh_id"),
            doh.cus_doh_fk.label("cus_id"),
            doh.doh_date.label("doh_date"),
            dli.ite_dli_fk.label("ite_id"),
            dli.idc_dli_fk.label("idc_id"),
            dli.dli_dimone.label("dim_one"),
            dli.dli_dimonevalue.label("dim_one_value"),
            dli.dli_dimtwo.label("dim_two"),
            dli.dli_dimtwovalue.label("dim_two_value"),
            uom.uom_symbol.label("uom_symbol"),
            func.sum(dli.dli_quantity).label("dli_quantity"),
        )
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

    # Se agrega el group by por cada uno de estos campos. La idea es mantener la agrupación por documento y dimensiones:
    order_history = order_history.group_by(
        doh.doh_id,
        doh.cus_doh_fk,
        doh.doh_date,
        dli.ite_dli_fk,
        dli.idc_dli_fk,
        dli.dli_dimone,
        dli.dli_dimonevalue,
        dli.dli_dimtwo,
        dli.dli_dimtwovalue,
        uom.uom_symbol,
    ).order_by(
        doh.doh_date.asc(),
        doh.doh_id.asc(),
    )

    rows = order_history.all()

    result: list[OrderHistorySchema] = []
    for row in rows:
        if row.idc_id is not None and row.idc_id != 0:
            idc_schema = IdcFormatSchema(
                idc_id=row.idc_id,
                idc_dim_one=row.dim_one,
                idc_dim_one_value=row.dim_one_value,
                idc_dim_two=row.dim_two,
                idc_dim_two_value=row.dim_two_value,
            )
        else:
            idc_schema = None

        result.append(
            OrderHistorySchema(
                referenciaCliente=str(row.cus_id),
                fechaCreacion=row.doh_date,
                referenciaProducto=str(row.ite_id),
                cantidad=row.dli_quantity,
                formatoDeVenta=(
                    str(row.uom_symbol) if row.uom_symbol is not None else None
                ),
                combination=idc_schema,
            )
        )

    return result


# def get_orderHistory(
#     db: Session, fromDate: datetime, UpToDate: datetime, customer: int | None = None
# ) -> list[OrderHistorySchema]:
#     idc_schema: IdcFormatSchema | None = None
#     if fromDate > UpToDate:
#         raise ValueError("fromDate cannot be greater than UpToDate")
#     order_history = (
#         db.query(doh, dli, uom)
#         .join(dli, dli.doh_dli_fk == doh.doh_id)
#         .outerjoin(uom, dli.uom_dli_fk == uom.uom_id)
#         .outerjoin(
#             dof,
#             dof.dof_doclinedestiny == dli.dli_id,
#         )
#         .filter(
#             # Aquí deberá ser un pedido o un albarán que no contenga un origen en un pedido.
#             or_(
#                 doh.doh_type == 2,
#                 and_(
#                     doh.doh_type == 3,
#                     or_(
#                         dof.dof_origintype.is_(None),
#                         dof.dof_origintype != 2,
#                     ),
#                 ),
#             ),
#             doh.doh_date >= fromDate,
#             doh.doh_date <= UpToDate,
#         )
#         .order_by(doh.doh_date.asc())
#     )
#     if customer is not None:
#         order_history = order_history.filter(doh.cus_doh_fk == customer)

#     rows = order_history.all()

#     result: list[OrderHistorySchema] = []
#     for doh_data, dli_data, uom_data in rows:
#         if dli_data.idc_dli_fk is not None and dli_data.idc_dli_fk != 0:
#             idc_schema = IdcFormatSchema(
#                 idc_id=dli_data.idc_dli_fk,
#                 idc_dim_one=dli_data.dli_dimone,
#                 idc_dim_one_value=dli_data.dli_dimonevalue,
#                 idc_dim_two=dli_data.dli_dimtwo,
#                 idc_dim_two_value=dli_data.dli_dimtwovalue,
#             )

#         result.append(
#             OrderHistorySchema(
#                 referenciaCliente=str(doh_data.cus_doh_fk),
#                 fechaCreacion=doh_data.doh_date,
#                 referenciaProducto=str(dli_data.ite_dli_fk),
#                 cantidad=dli_data.dli_quantity,
#                 formatoDeVenta=(
#                     str(uom_data.uom_symbol) if uom_data is not None else None
#                 ),
#                 combination=idc_schema,
#             )
#         )

#     return result
