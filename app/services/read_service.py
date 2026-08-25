from sqlalchemy.orm import Session, aliased

from app.db.models import (
    Item,
    UnitOfMeasure,
    UnitOfMeasureCategory,
    UnitOfMeasureConversion,
)
from app.schemas.product import ProductFormatSchema, ProductSchema


# ------------- LECTURA DE PRODUCTOS ------------ #
# Calculo de unidades por formato.
def calculate_units_per_format(operation: int, factor: float) -> float:
    if operation == 1:
        return factor
    if operation == 2:
        return 1 / factor
    return 1


# Obtención de productos.
def get_products(db: Session) -> list[ProductSchema]:
    # 2026-08-25 Se crean 2 alias nuevos para la construcción de la consulta.
    UomStock = aliased(UnitOfMeasure)
    UomConversion = aliased(UnitOfMeasure)
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
            Item,
            UnitOfMeasureCategory,
            UnitOfMeasureConversion,
            UomStock,
            UomConversion,
        )
        .outerjoin(
            UnitOfMeasureCategory,
            Item.umc_ite_fk == UnitOfMeasureCategory.umc_id,
        )
        .outerjoin(
            UnitOfMeasureConversion,
            (UnitOfMeasureConversion.umc_umo_fk == UnitOfMeasureCategory.umc_id)
            & (UnitOfMeasureConversion.uom_umo_fk == UnitOfMeasureCategory.uom_umc_fk),
        )
        .outerjoin(
            UomStock,
            UnitOfMeasureCategory.uom_umc_fk == UomStock.uom_id,
        )
        .outerjoin(
            UomConversion,
            UnitOfMeasureConversion.uom_umo_fk2 == UomConversion.uom_id,
        )
        .filter(
            Item.ite_sale.is_(True),
            Item.ite_locked.is_(False),
            Item.ite_discontinued.is_(False),
        )
        .all()
    )
    # Los productos los almacenamos en un diccionario para guardarlos según cada registro.
    # {'ite_id': {Esquema}}
    products: dict[str, ProductSchema] = {}

    for item, category, conversion, uom_stock, uom_conversion in items:

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
    return list(products.values())
    # return [
    #     ProductSchema(referencia=item.ite_id, nombre=item.ite_name or "")
    #     for item in items
    # ]
