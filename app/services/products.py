from fastapi import HTTPException
from sqlalchemy.orm import Session, aliased

from app.api.v1.schemas.products.responses import (
    IdcFormatSchema,
    ProductFormatSchema,
    ProductSchema,
)
from app.db.tenant_models import TenantModels


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
def get_products(db: Session, models: TenantModels) -> list[ProductSchema]:
    # 2026-08-25 Se crean 2 alias nuevos para la construcción de la consulta.
    UomStock = aliased(models.uom)
    UomConversion = aliased(models.uom)

    # 2026-09-16 Creo variables globales para los modelos a utilizar. Evitando repetir models.ite por todos lados.
    ite = models.ite
    idc = models.idc
    umc = models.umc
    umo = models.umo

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
                variable=item.ite_variable,
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
            products[item.ite_id].combinations.append(
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


def get_product_by_id(
    db: Session, item_id: str, models: TenantModels
) -> ProductSchema | None:
    new_item: ProductSchema | None = None

    ite = models.ite
    idc = models.idc
    umc = models.umc
    umo = models.umo
    uom = models.uom

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
    item_data = (
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
            ite.ite_id == item_id,
        )
        .first()
    )
    # Los productos los almacenamos en un diccionario para guardarlos según cada registro.
    # {'ite_id': {Esquema}}
    # products: dict[str, ProductSchema] = {}
    if item_data is None:
        # No se encontró el artículo
        raise HTTPException(
            status_code=404,
            detail=f"Product '{item_id}' not found",
        )

    item, category, conversion, uom_stock, uom_conversion = item_data  # noqa: RUF059

    new_item = ProductSchema(
        referencia=item.ite_id,
        nombre=item.ite_name,
        formatosDeVenta=[],
        variable=item.ite_variable,
    )

    # La unidad de stock se agrega una única vez.
    if uom_stock is not None:
        new_item.formatosDeVenta.append(
            ProductFormatSchema(
                referenciaFormato=str(uom_stock.uom_symbol),
                nombre=uom_stock.uom_unit,
                unidadesPorFormato=1,
            )
        )
    # Cada fila puede representar una conversión distinta.
    if conversion is not None and uom_conversion is not None:
        new_item.formatosDeVenta.append(
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
        new_item.combinations.append(
            IdcFormatSchema(
                idc_id=idc_id,
                idc_dim_one=idc_dimone,
                idc_dim_one_value=idc_dimonevalue,
                idc_dim_two=idc_dimtwo,
                idc_dim_two_value=idc_dimtwovalue,
            )
        )

    return new_item
    # return [
    #     ProductSchema(referencia=item.ite_id, nombre=item.ite_name or "")
    #     for item in items
    # ]
