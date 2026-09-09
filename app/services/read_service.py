from datetime import datetime

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session, aliased

from app.db.models import (
    add,
    age,
    con,
    cus,
    dli,
    dof,
    doh,
    epl,
    idc,
    ite,
    umc,
    umo,
    uom,
)
from app.schemas.commercial_agents.responses import AgentSchema
from app.schemas.customers.responses import CustomerSchema
from app.schemas.orders.responses import OrderHistorySchema
from app.schemas.products.responses import (
    IdcFormatSchema,
    ProductFormatSchema,
    ProductSchema,
)


# ------------- LECTURA DE PRODUCTOS ------------ #
# Calculo de unidades por formato.
def calculate_units_per_format(operation: int, factor: float) -> float:
    # Gestión de error, valor = 0. Además si no entra en uno u otro deberé gestionarlo.
    if factor == 0:
        raise ValueError("The conversion factor cannot be zero")
    if operation == 1:
        return factor
    if operation == 2:
        return 1 / factor
    raise ValueError(f"Unsupported conversion operation: {operation}")


# Obtención de productos.
def get_products(db: Session) -> list[ProductSchema]:
    # 2026-08-25 Se crean 2 alias nuevos para la construcción de la consulta.
    UomStock = aliased(uom)
    UomConversion = aliased(uom)
    # En pide facil necesitan saber que son artículos ya activos que se pueden vender. Por ello se agregan los filtros correspondientes.
    # La consulta por base de datos sería esta:
    #     SELECT uom1.unit, umc_ite_fk, uom_umc_fk, uom1.uom_symbol, uom_umo_fk2,uom2.uom_symbol, umo_operation, umo_factor, ite_sale, ite_locked,      ite_discontinued, * FROM "ITEM_ITE"
    #  LEFT JOIN "UNITOFMEASURECATEGORY_UMC" ON umc_ite_fk = umc_id
    #  LEFT JOIN "UNITOFMEASURECONVERSION_UMO" ON umc_umo_fk = umc_id AND uom_umo_fk = uom_umc_fk
    #  LEFT JOIN "UNITOFMEASURE_UOM" uom1 ON uom_umc_fk = uom1.uom_id
    #  LEFT JOIN "UNITOFMEASURE_UOM" uom2 ON uom_umo_fk2 = uom2.uom_id
    #  WHERE ite_sale IS FALSE AND ite_locked IS FALSE AND ite_discontinued IS FALSE
    items = (
        db.query(
            ite,
            umc,
            umo,
            UomStock,
            UomConversion,
        )
        .outerjoin(
            umc,
            ite.umc_ite_fk == umc.umc_id,
        )
        .outerjoin(
            umo,
            (umo.umc_umo_fk == umc.umc_id) & (umo.uom_umo_fk == umc.uom_umc_fk),
        )
        .outerjoin(
            UomStock,
            umc.uom_umc_fk == UomStock.uom_id,
        )
        .outerjoin(
            UomConversion,
            umo.uom_umo_fk2 == UomConversion.uom_id,
        )
        .filter(
            ite.ite_sale.is_(True),
            ite.ite_locked.is_(False),
            ite.ite_discontinued.is_(False),
        )
        .all()
    )
    # Los productos los almacenamos en un diccionario para guardarlos según cada registro.
    # {'ite_id': {Esquema}}
    products: dict[str, ProductSchema] = {}

    for item, category, conversion, uom_stock, uom_conversion in items:
        print(item.ite_id)
        # Si todavía no existe el producto, lo creamos.
        if item.ite_id not in products:
            products[item.ite_id] = ProductSchema(
                referencia=item.ite_id,
                nombre=item.ite_name,
                formatosDeVenta=[],
            )

            # La unidad de stock se agrega una única vez.
            if uom_stock is not None:
                products[item.ite_id].formatosDeVenta.append(
                    ProductFormatSchema(
                        referenciaFormato=str(uom_stock.uom_symbol),
                        nombre=uom_stock.uom_unit,
                        unidadesPorFormato=1,
                    )
                )
        # Cada fila puede representar una conversión distinta.
        if conversion is not None and uom_conversion is not None:
            products[item.ite_id].formatosDeVenta.append(
                ProductFormatSchema(
                    referenciaFormato=str(uom_conversion.uom_symbol),
                    nombre=uom_conversion.uom_unit,
                    unidadesPorFormato=calculate_units_per_format(
                        conversion.umo_operation,
                        conversion.umo_factor,
                    ),
                )
            )
        # Formateamos y obtenemos todas las dimensiones del artículo que no se encuentran bloqueadas o descatalogadas.
        idc_data = (
            db.query(
                idc.idc_id,
                idc.idc_dimone,
                idc.idc_dimonevalue,
                idc.idc_dimtwo,
                idc.idc_dimtwovalue,
            )
            .filter(
                idc.idc_locked.is_(False),
                idc.idc_discontinued.is_(False),
                idc.ite_idc_fk == item.ite_id,
            )
            .all()
        )
        for (
            idc_id,
            idc_dimone,
            idc_dimonevalue,
            idc_dimtwo,
            idc_dimtwovalue,
        ) in idc_data:
            print("idc_dimone ", idc_dimone)
            products[item.ite_id].idc_combination.append(
                IdcFormatSchema(
                    idc_id=idc_id,
                    idc_dim_one=idc_dimone,
                    idc_dim_one_value=idc_dimonevalue,
                    idc_dim_two=idc_dimtwo,
                    idc_dim_two_value=idc_dimtwovalue,
                )
            )

    return list(products.values())
    # return [
    #     ProductSchema(referencia=item.ite_id, nombre=item.ite_name or "")
    #     for item in items
    # ]


# Primero se obtienen los clientes, luego se obtienen cada uno de los telefonos disponibles, tanto
# de contactos como de direcciones.
# Luego se organizan los telefonos para que incluya primero los de los contactos, y en caso de que aún quede espacio (Hasta 3)
# se incluirán los de las direcciones.
def get_customers(db: Session) -> list[CustomerSchema]:
    customer_data = (
        db.query(cus, add, con)
        .outerjoin(con, (cus.cus_id == con.cus_con_fk))
        .outerjoin(add, (cus.cus_id == add.cus_add_fk))
        .order_by(cus.cus_id.asc(), add.add_invoice.desc(), con.con_id.asc())
        .all()
    )

    customers = {}
    for customer, address, contact in customer_data:
        # En caso de que no exista, lo añadimos.
        if customer.cus_id not in customers:
            customers[customer.cus_id] = {
                "referencia": str(customer.cus_id),
                "nombre": customer.cus_corporatename,
                "contact_phones": [],
                "address_phones": [],
            }
        if contact is not None:
            for phone in (contact.con_phone1, contact.con_phone2):
                if (
                    phone is not None
                    and phone not in customers[customer.cus_id]["contact_phones"]
                ):
                    customers[customer.cus_id]["contact_phones"].append(phone)
        if address is not None:
            for phone in (address.add_phone1, address.add_phone2):
                if (
                    phone is not None
                    and phone not in customers[customer.cus_id]["address_phones"]
                ):
                    customers[customer.cus_id]["address_phones"].append(phone)
    # Loopeamos por el resultado filtrando los telefonos correspondientes.
    result: list[CustomerSchema] = []

    for customer in customers.values():
        # Se agregan los primeros 3 telefonos en contactos.
        phones = customer["contact_phones"][:3]
        # Si todavía no se llega a 3. Agrego telefonos hasta 3.
        if len(phones) < 3:
            for phone in customer["address_phones"]:
                if phone not in phones:
                    phones.append(phone)

                if len(phones) == 3:
                    break

        result.append(
            CustomerSchema(
                referencia=customer["referencia"],
                nombre=customer["nombre"],
                telefonos=phones,
            )
        )

    return result


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


# ----- Lecturas opcionales.
# Obtención de comerciales.
def get_commercial_agent(db: Session) -> list[AgentSchema]:
    result = []
    age_data = (
        db.query(age.age_id, age.age_name, add.add_phone1)
        .outerjoin(epl, (epl.epl_id == age.epl_age_fk))
        .outerjoin(add, (add.epl_add_fk == epl.epl_id))
        .order_by(age.age_id)
        .all()
    )
    for age_id, age_name, add_phone1 in age_data:
        result.append(
            AgentSchema(referencia=str(age_id), nombre=age_name, telefono=add_phone1)
        )
    return result
