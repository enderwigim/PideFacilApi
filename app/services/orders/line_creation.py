from decimal import Decimal

from sqlalchemy import or_, text
from sqlalchemy.orm import Session, aliased

from app.db.models import (
    cur,
    cus,
    dli,
    doh,
    idc,
    ite,
    tas,
    ttv,
    umc,
    umo,
    uom,
)
from app.schemas.orders.requests import CreationLineSchema


def create_order_lines(db: Session, lines: list[CreationLineSchema], order: doh):
    nDohID: int
    nDliID: int
    nOrder: int
    sIteID: str
    sDescription: str
    xQuantity: Decimal
    xQuantity2: Decimal
    nUomStock: int
    nUomVariable: int
    nUomDliFk: int
    nUomDliFk2: int
    nOperation: int
    xFactor: Decimal | None = None
    nDecimalCantidad: int
    nDecimalCantidad2: int
    nDecimalPrice: int
    nDecimalPrice2: int
    nDecimalCost: int
    nDecimalCost2: int
    nIdcDim1: int
    sIdcDimValue1: str
    nIdcDim2: int
    sIdcDimValue2: str
    nTas: int  # Sistema de impuestos del documento en el que estoy impotando.
    bSale: bool
    bVariable: bool
    nPlcCusFk: int | None = None
    nTatItefk: int
    nTatItefk2: int
    sDohDate: str
    xIRPF: Decimal | None = None
    nWarDliFk: int | None = None
    sUom2Symbol: str
    nOrder: int
    nTasTax: int | None = None
    bTasApplyRate2: bool = False
    nCusID: int | None = None
    nCurDohFk: int | None = None
    nDecimalTotalamount: int = 6  # Por defecto.

    nOrder = 1
    nDohID = order.doh_id
    nWarDliFk = order.war_doh_fk
    nTas = order.tas_doh_fk
    sDohDate = order.doh_date
    xIRPF = order.doh_holdrate
    nCusID = order.cus_doh_fk
    nCurDohFk = order.cur_doh_fk
    # Validamos si el documento tiene recargo de equivalencia o no.
    tas_data = (
        db.query(tas.tas_tax, tas.tas_applyrate2).filter(tas.tas_id == nTas).first()
    )
    if tas_data is not None:
        nTasTax = tas_data.tas_tax
        bTasApplyRate2 = tas_data.tas_applyrate2

    # Calculamos la tarifa del cliente (En caso de tener)
    price_list_data = db.query(cus).filter(order.cus_doh_fk == cus.cus_id).first()
    if price_list_data:
        nPlcCusFk = price_list_data.plc_cus_fk

    # Validamos los decimales del totalamount. Esto se realizará según la divisa del documento.
    # Por defecto pondremos 2.
    cur_data = db.query(cur.cur_decimals).filter(cur.cur_id == nCurDohFk).first()
    if cur_data is not None:
        nDecimalTotalamount = cur_data.cur_decimals

    for line in lines:

        # Declaro las variables que me interesan que se inicialicen en el bucle.
        nDliID: int

        sIteID: str
        sDescription: str
        xQuantity: Decimal | None = None
        xQuantity2: Decimal | None = None
        nUomStock: int
        nUomDliFk: int
        nUomDliFk2: int
        nOperation: int
        xFactor: Decimal | None = None
        nDecimalCantidad: int
        nDecimalCantidad2: int
        nDecimalPrice: int
        nDecimalPrice2: int
        nDecimalCost: int
        nDecimalCost2: int
        nIdcIte: int = 0
        # 2026-08-28 Comentado.
        # nDioIte1: int = 0
        # nDioIte2: int = 0
        nIdcID: int | None = None
        nIdcDim1: int | None = None
        sIdcDimValue1: str | None = None
        nIdcDim2: int | None = None
        sIdcDimValue2: str | None = None
        bSale: bool
        bVariable: bool
        nPlcCusFk: int | None = None
        nTatItefk: int
        nTatItefk2: int
        nDiscount1: Decimal = 0
        nDiscount2: Decimal = 0
        nDiscount3: Decimal = 0
        nDiscountUM: Decimal = 0

        sUom2Symbol: str

        new_line = dli()

        # Primero obtengo el primer valor.
        nDliID = db.execute(text("SELECT nextval('DOCLINE_DLI_DLI_ID')")).scalar_one()
        # nOrder = db.query(func.max(DocLine.dli_order)).scalar()
        # if nOrder is None:
        #     nOrder = 1
        # else:
        #     nOrder += 1

        # Se valida la existencia del artículo en la base de datos.
        sIteID = line.referenciaProducto
        item_query = (
            db.query(
                ite.ite_name,
                ite.ite_decimalunit,
                ite.ite_decimalsale,
                ite.ite_decimalpurchase,
                ite.ite_sale,
                ite.ite_variable,
                ite.uom_ite_fk,
                # ite.dio_ite_fk,
                # ite.dit_ite_fk,
                idc.idc_id,
                ite.tat_ite_fk,
                ite.tat_ite_fk2,
                ite.ite_weight,
                ite.uom_ite_fk5,
            )
            .outerjoin(idc, ite.ite_id == idc.ite_idc_fk)
            .filter(
                ite.ite_id == sIteID,
                ite.ite_discontinued.is_(False),
                ite.ite_locked.is_(False),
            )
            .first()
        )
        if item_query is None:
            raise ValueError(f"Item: '{sIteID}' not found")
        else:
            sDescription = item_query.ite_name
            nDecimalCantidad = item_query.ite_decimalunit
            nDecimalCantidad2 = item_query.ite_decimalunit
            nDecimalPrice = item_query.ite_decimalsale
            nDecimalPrice2 = item_query.ite_decimalsale
            nDecimalCost = item_query.ite_decimalpurchase
            nDecimalCost2 = item_query.ite_decimalpurchase
            bSale = item_query.ite_sale
            bVariable = item_query.ite_variable
            nUomStock = item_query.uom_ite_fk
            # Se agrega idc a la consulta, para simplemente saber si el artículo tiene combinaciones.
            nIdcIte = item_query.idc_id
            # nDioIte1 = item_query.dio_ite_fk
            # nDioIte2 = item_query.dit_ite_fk
            nTatItefk = item_query.tat_ite_fk
            nTatItefk2 = item_query.tat_ite_fk2
            xWeightPerPiece = item_query.ite_weight
            nUomVariable = item_query.uom_ite_fk5

        # Antes de seguir valido que el artículo se vende. En caso contrario, continuo con el siguiente.
        if bSale is False:
            continue

        ttv_data = db.query(ttv.ttv_rate, ttv.ttv_rate2)
        match nTasTax:
            case 1:
                ttv_data = (
                    ttv_data.filter(
                        ttv.tat_ttv_fk == nTatItefk,
                        or_(
                            ttv.ttv_date >= sDohDate,
                            ttv.ttv_date.is_(None),
                        ),
                    )
                    .order_by(ttv.ttv_id.asc())
                    .first()
                )
                if ttv_data is not None:
                    xTtvRate1 = ttv_data.ttv_rate
                    xTtvRate2 = ttv_data.ttv_rate2
                    nTatDliFkAux = nTatItefk
                    xLineTaxRate1 = xTtvRate1
                    if bTasApplyRate2 is True:
                        xLineTaxRate2 = xTtvRate2
                    else:
                        xLineTaxRate2 = 0
            case 2:
                ttv_data = (
                    ttv_data.filter(
                        ttv.tat_ttv_fk == nTatItefk2,
                        or_(
                            ttv.ttv_date >= sDohDate,
                            ttv.ttv_date.is_(None),
                        ),
                    )
                    .order_by(ttv.ttv_id.asc())
                    .first()
                )
                if ttv_data is not None:
                    xTtvRate1 = ttv_data.ttv_rate
                    xTtvRate2 = ttv_data.ttv_rate2
                    nTatDliFkAux = nTatItefk2
                    xLineTaxRate1 = xTtvRate1
                    if bTasApplyRate2 is True:
                        xLineTaxRate2 = xTtvRate2
                    else:
                        xLineTaxRate2 = 0
            case 3:
                nTatDliFkAux = 1
                xLineTaxRate1 = 0
                xLineTaxRate2 = 0
        xLineTaxRate3 = xIRPF
        # CASO CON COMBINACIONES.
        # Si el artículo tiene combinaciones, buscaremos la que nos haya pasado por parametro. Esta será la que insertemos en el artículo.
        # en caso de que el artículo no tenga IDC, entonces sigo.
        # Si el artículo no encuentra la combinación solicitada, paro el proceso. No puedo insertarlo sin combinación.
        if nIdcIte != 0:
            idc_data = db.query(
                idc.idc_id,
                idc.idc_dimone,
                idc.idc_dimonevalue,
                idc.idc_dimtwo,
                idc.idc_dimtwovalue,
            )
            # Al especificar una combinación búsco por esta.
            if line.combination is not None:
                idc_data = idc_data.filter(idc.idc_id == line.combination).first()
            else:
                # Si no está aclarado en la solicitud, se agrega el por defecto.
                idc_data = idc_data.filter(
                    idc.ite_idc_fk == sIteID,
                    idc.idc_default.is_(True),
                    idc.idc_discontinued.is_(False),
                ).first()

            print("idc_data ", idc_data)
            if idc_data is not None:
                nIdcID = idc_data.idc_id
                nIdcDim1 = idc_data.idc_dimone
                sIdcDimValue1 = idc_data.idc_dimonevalue
                nIdcDim2 = idc_data.idc_dimtwo
                sIdcDimValue2 = idc_data.idc_dimtwovalue
            else:
                raise ValueError(
                    f"Combination '{line.combination}' for item '{line.referenciaProducto}'"
                    f" doesn't exist'"
                )
        else:
            nIdcID = 0
            nIdcDim1 = 0
            sIdcDimValue1 = ""
            nIdcDim2 = 0
            sIdcDimValue2 = ""

        if line.cantidad:
            xQuantity = line.cantidad

        if line.formatoDeVenta:
            sUom2Symbol = line.formatoDeVenta
            # Antes de obtener los datos correspondientes a la conversión de unidades de medida. Vale la pena comprobar si se ha utilizado
            # la misma unidad de medida que la de stock.
            nUomParam = get_uom_id_by_symbol(db, sUom2Symbol)
            if nUomParam == 0:
                raise ValueError(f"Unit '{line.formatoDeVenta}' " f"doesn't exist'")
            else:
                # En caso de que obtengamos la misma unidad de stock que la del artículo. No realizamos ningún calculo.
                if nUomParam == nUomStock:
                    nUomDliFk = nUomStock
                    nUomDliFk2 = nUomStock
                    xQuantity2 = xQuantity
                else:
                    uom_data = get_item_uom_data(db, sIteID, sUom2Symbol)
                    if uom_data is not None:
                        nUomDliFk = uom_data["uom_dli_fk"]
                        nUomDliFk2 = uom_data["uom_dli_fk2"]
                        nOperation = uom_data["umo_operation"]
                        xFactor: Decimal = uom_data["umo_factor"]
                        nDecimalCantidad2 = uom_data["uom_decimalunit"]

                        xQuantity2 = convert_quantity_to_stock(
                            xQuantity, nOperation, xFactor
                        )
                    else:
                        raise ValueError(
                            f"Unit '{line.formatoDeVenta}' "
                            f"not found for item '{sIteID}'"
                        )
        # Si no se nos pasan datos correspondinetes a unidades de medida, dejamos la unidad de stock del artículo.
        else:
            if bVariable is True:
                nUomDliFk = nUomVariable
                nUomDliFk2 = nUomStock
            else:
                nUomDliFk = nUomStock
                nUomDliFk2 = nUomStock
                xQuantity2 = xQuantity
        # Obtengo los precios y costes:
        prices_costs_data = (
            db.execute(
                text("""
                SELECT *
                FROM isql_Get_Prices_And_Costs_By_Default(
                    :purchase_or_sale,
                    :doc_type,
                    :customer_id,
                    :price_list,
                    :param5,
                    :item_id,
                    :item_dim_one,
                    :item_dim_one_value,
                    :item_dim_two,
                    :item_dim_two_value,
                    :batch_number,
                    :serial_number,
                    :expiration_date,
                    :item_uom
                )
                AS MyResult(
                    Price2 numeric,
                    Cost2 numeric,
                    Price numeric,
                    Cost numeric
                )
                """),
                {
                    "purchase_or_sale": 2,
                    "doc_type": 2,
                    "customer_id": order.cus_doh_fk,
                    "price_list": nPlcCusFk,
                    "param5": 0,
                    "item_id": sIteID,
                    "item_dim_one": nIdcDim1,
                    "item_dim_one_value": sIdcDimValue1,
                    "item_dim_two": nIdcDim2,
                    "item_dim_two_value": sIdcDimValue2,
                    "batch_number": None,
                    "serial_number": None,
                    "expiration_date": None,
                    "item_uom": nUomDliFk,
                },
            )
            .mappings()
            .first()
        )
        if prices_costs_data is None:
            raise ValueError(f"Prices and costs not found for item '{sIteID}'")

        xItemPrice2 = prices_costs_data["price2"]
        xItemCostPrice2 = prices_costs_data["cost2"]
        xItemPrice = prices_costs_data["price"]
        xItemCostPrice = prices_costs_data["cost"]

        # Si es de peso variable
        if bVariable is True:
            # En caso de que el usuario rellene el peso por pieza lo colocaremos aquí.
            if line.peso_pieza is not None:
                xWeightPerPiece = line.peso_pieza
            xQuantityToInsert = xQuantity
            xQuantityToInsert2 = xQuantity * xWeightPerPiece
            print(xQuantityToInsert2)
            xPriceToInsert = xItemPrice * xWeightPerPiece
            xPriceToInsert2 = xItemPrice
            xCostToInsert = xItemCostPrice * xWeightPerPiece
            xCostToInsert2 = xItemCostPrice
            xImporteLinea = xPriceToInsert2 * xQuantityToInsert2
        else:
            xQuantityToInsert = xQuantity
            xQuantityToInsert2 = xQuantity2
            xPriceToInsert = xItemPrice
            xPriceToInsert2 = xItemPrice2
            xCostToInsert = xItemCostPrice
            xCostToInsert2 = xItemCostPrice2
            xImporteLinea = xItemPrice * xQuantityToInsert

        if line.discounts is not None:
            nDiscount1 = line.discounts.get("dto1", 0)
            nDiscount2 = line.discounts.get("dto2", 0)
            nDiscount3 = line.discounts.get("dto3", 0)
            nDiscountUM = line.discounts.get("dtoUM", 0)

        # Calculo un rangeOffer sencillo. No estoy tan seguro que no debamos aplicar descuentos.
        sRangeOffer = f"{xPriceToInsert};{xPriceToInsert2};{xPriceToInsert};{xPriceToInsert2};0;0;0;0"
        new_line.dli_id = nDliID
        new_line.dli_order = nOrder
        new_line.doh_dli_fk = nDohID
        new_line.ite_dli_fk = sIteID
        new_line.dli_description = sDescription
        new_line.dli_descriptionchange = False
        new_line.dli_quantity = xQuantityToInsert
        new_line.dli_quantity2 = xQuantityToInsert2
        new_line.uom_dli_fk = nUomDliFk
        new_line.war_dli_fk = nWarDliFk
        new_line.dli_price = xPriceToInsert
        new_line.dli_costprice = xCostToInsert
        new_line.uom_dli_fk2 = nUomDliFk2
        new_line.dli_price2 = xPriceToInsert2
        new_line.dli_costprice2 = xCostToInsert2
        new_line.tat_dli_fk = nTatDliFkAux
        new_line.dli_taxrate1 = xLineTaxRate1
        new_line.dli_taxrate2 = xLineTaxRate2
        new_line.dli_taxrate3 = xLineTaxRate3
        new_line.dli_totalamount = xImporteLinea
        new_line.dli_decimalquantity = nDecimalCantidad
        new_line.dli_decimalquantity2 = nDecimalCantidad2
        new_line.dli_decimalprice = nDecimalPrice
        new_line.dli_decimalprice2 = nDecimalPrice2
        new_line.dli_decimalcost = nDecimalCost
        new_line.dli_decimalcost2 = nDecimalCost2
        new_line.dli_decimaltotalamount = nDecimalTotalamount
        new_line.dli_undelivered = xQuantity
        new_line.dli_delivered = 0
        # new_line.wab_dli_fk  NO NECESITO UBICACIONES EN PEDIDO.
        new_line.dli_rangeoffer = sRangeOffer
        # new_line.dli_weight // NECESITO???

        # Revisar Debería calcular los descuentos correspondientes con el articulo, cliente y condiciones de venta.
        new_line.dli_discountcashunit = 0
        new_line.dli_discount = 0
        new_line.idc_dli_fk = nIdcID
        new_line.dli_dimone = nIdcDim1
        new_line.dli_dimonevalue = sIdcDimValue1
        new_line.dli_dimtwo = nIdcDim2
        new_line.dli_dimtwovalue = sIdcDimValue2

        db.add(new_line)
        db.flush()

        db.refresh(new_line)

        # Aplicar luego.
        # # Una vez terminada la inserción debemos calcular las promociones. Esto se puede realizar con un función de base de datos existente.
        # # isql_Set_Calculate_Offers_In_Document
        result = calculate_offers_in_document(
            db=db,
            nMode=0,  # INSERCIÓN
            nIDDoc=nDohID,
            nPurchaseOrSale=2,
            nSupplierOrCustomer=int(nCusID),
            nDocumentType=2,
            sDateDocument=sDohDate,
            nIDLine=nDliID,
            sItem=sIteID,
            nDimOne=nIdcDim1,
            sDimOneValue=sIdcDimValue1,
            nDimTwo=nIdcDim2,
            sDimTwoValue=sIdcDimValue2,
            sBatchNumber="",
            sSerialNumber="",
            sExpirationDate="2999-01-01",
            nQuantity=xQuantityToInsert,
            nUM=nUomDliFk,
            nQuantity2=xQuantityToInsert2,
            nUM2=nUomDliFk2,
            nPrice=xPriceToInsert,
            nPrice2=xPriceToInsert2,
            nCost=xCostToInsert,
            nCost2=xCostToInsert2,
            nDiscount1=nDiscount1,
            nDiscount2=nDiscount2,
            nDiscount3=nDiscount3,
            nDecimalPrice=nDecimalPrice,
            nDecimalPrice2=nDecimalPrice2,
            nDecimalTotalAmount=nDecimalTotalamount,
            sRangeOffer=sRangeOffer,
            nTaxRate1=xLineTaxRate1,
            nTaxRate2=xLineTaxRate2,
            nTaxRate3=xLineTaxRate3,
            nParent=0,
            sAuto=False,
            bLinesDocOrigin=False,
            bLinesDocDestiny=False,
            nDiscountCashUM=nDiscountUM,
        )
        if result is True:
            print("OAAAAA")

        # # nDecimalPrice
        # # nDecimalPrice2
        # # nDecimalTotalAmount
        # # sRangeOffer
        # # xLineTaxRate1
        # # xLineTaxRate2
        # # xLineTaxRate3
        # nParent = 0
        # sAuto = "False"
        # # sLinesDocOrigin --- Vacío
        # # sLinesDocDestiny ---Vacío
        # # nDiscountCashUM ---Vacío??

        nOrder += 1


from sqlalchemy.orm import Session


def calculate_offers_in_document(
    db: Session,
    nMode,
    nIDDoc,
    nPurchaseOrSale,
    nSupplierOrCustomer: int,
    nDocumentType,
    sDateDocument,
    nIDLine,
    sItem,
    nDimOne,
    sDimOneValue,
    nDimTwo,
    sDimTwoValue,
    sBatchNumber,
    sSerialNumber,
    sExpirationDate,
    nQuantity,
    nUM,
    nQuantity2,
    nUM2,
    nPrice,
    nPrice2,
    nCost,
    nCost2,
    nDiscount1,
    nDiscount2,
    nDiscount3,
    nDecimalPrice,
    nDecimalPrice2,
    nDecimalTotalAmount,
    sRangeOffer,
    nTaxRate1,
    nTaxRate2,
    nTaxRate3,
    nParent,
    sAuto,
    bLinesDocOrigin,
    bLinesDocDestiny,
    nDiscountCashUM,
) -> bool:
    query = text("""
        SELECT isql_Set_Calculate_Offers_In_Document(
            :mode,:id_doc,:purchase_or_sale,:supplier_or_customer,:document_type,:date_document,:id_line,
            :item,:dim_one,:dim_one_value,:dim_two,:dim_two_value,:batch_number,:serial_number,:expiration_date,
            :quantity,:um,:quantity2,:um2,:price,:price2,:cost,:cost2,:discount1,:discount2,:discount3,
            :decimal_price,:decimal_price2,:decimal_total_amount,:range_offer,
            :tax_rate1,:tax_rate2,:tax_rate3,
            :parent,:auto,:lines_doc_origin,:lines_doc_destiny,:discount_cash_um
        ) AS "MyResult"
    """)

    params = {
        "mode": nMode,
        "id_doc": nIDDoc,
        "purchase_or_sale": nPurchaseOrSale,
        "supplier_or_customer": nSupplierOrCustomer,
        "document_type": nDocumentType,
        "date_document": sDateDocument,
        "id_line": nIDLine,
        "item": sItem,
        "dim_one": nDimOne,
        "dim_one_value": sDimOneValue,
        "dim_two": nDimTwo,
        "dim_two_value": sDimTwoValue,
        "batch_number": sBatchNumber,
        "serial_number": sSerialNumber,
        "expiration_date": sExpirationDate,
        "quantity": nQuantity,
        "um": nUM,
        "quantity2": nQuantity2,
        "um2": nUM2,
        "price": nPrice,
        "price2": nPrice2,
        "cost": nCost,
        "cost2": nCost2,
        "discount1": nDiscount1,
        "discount2": nDiscount2,
        "discount3": nDiscount3,
        "decimal_price": nDecimalPrice,
        "decimal_price2": nDecimalPrice2,
        "decimal_total_amount": nDecimalTotalAmount,
        "range_offer": sRangeOffer,
        "tax_rate1": nTaxRate1,
        "tax_rate2": nTaxRate2,
        "tax_rate3": nTaxRate3,
        "parent": nParent,
        "auto": sAuto,
        "lines_doc_origin": bLinesDocOrigin,
        "lines_doc_destiny": bLinesDocDestiny,
        "discount_cash_um": nDiscountCashUM,
    }
    # compiled = query.compile(dialect=db.get_bind().dialect)

    # raw_connection = db.connection().connection.driver_connection

    # with raw_connection.cursor() as cursor:
    #     sql_debug = cursor.mogrify(str(compiled), params).decode("utf-8")

    # print("\n========== QUERY DEBUG ==========")
    # print(sql_debug)
    # print("=================================\n")
    result = db.execute(query, params).scalar_one_or_none()

    return bool(result) if result is not None else False


def get_uom_id_by_symbol(db: Session, uom_symbol):
    # A partir de un simbolo nos devuelve el ID de la tabla UNITOFMEASURE_UOM. En caso de que dicho simbolo no se encuentre, devuelve 0.
    uom_data = (
        db.query(uom.uom_id).filter(uom.uom_symbol.ilike(uom_symbol.strip())).first()
    )
    if uom_data is not None:
        return uom_data.uom_id
    else:
        return 0


def get_item_uom_data(
    db: Session,
    item_id: str,
    uom_symbol: str,
):
    UomConversion = aliased(uom)

    result = (
        db.query(
            umo.uom_umo_fk2.label("uom_dli_fk"),
            umc.uom_umc_fk.label("uom_dli_fk2"),
            umo.umo_operation.label("umo_operation"),
            umo.umo_factor.label("umo_factor"),
            UomConversion.uom_decimalunit.label("uom_decimalunit"),
        )
        # Le decimos explícitamente que ITEM_ITE es el FROM principal
        .select_from(ite)
        .outerjoin(
            umc,
            ite.umc_ite_fk == umc.umc_id,
        )
        .outerjoin(
            umo,
            (umo.umc_umo_fk == umc.umc_id) & (umo.uom_umo_fk == umc.uom_umc_fk),
        )
        .outerjoin(
            UomConversion,
            umo.uom_umo_fk2 == UomConversion.uom_id,
        )
        .filter(
            ite.ite_id == item_id, UomConversion.uom_symbol.ilike(uom_symbol.strip())
        )
        .first()
    )

    if result is None:
        return None

    return dict(result._mapping)


def convert_quantity_to_stock(
    quantity: Decimal,
    operation: int,
    factor: Decimal,
) -> Decimal:
    if factor == 0:
        raise ValueError("The conversion factor cannot be zero")

    # UnidadStock * factor = UnidadConvertida
    if operation == 1:
        return quantity / factor

    # UnidadStock / factor = UnidadConvertida
    if operation == 2:
        return quantity * factor

    raise ValueError(f"Unsupported conversion operation: {operation}")
