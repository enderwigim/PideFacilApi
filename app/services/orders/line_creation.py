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
    n_order: int
    n_tas: int  # Sistema de impuestos del documento en el que estoy impotando.
    n_plc_cus_fk: int | None = None
    s_doh_date: str
    x_irpf: Decimal | None = None
    n_war_dli_fk: int | None = None
    n_tas_tax: int | None = None
    b_tas_apply_rate2: bool = False
    n_cus_id: int | None = None
    n_cur_doh_fk: int | None = None

    n_order = 1
    n_doh_id = order.doh_id
    n_war_dli_fk = order.war_doh_fk
    n_tas = order.tas_doh_fk
    s_doh_date = order.doh_date
    x_irpf = order.doh_holdrate
    n_cus_id = order.cus_doh_fk
    n_cur_doh_fk = order.cur_doh_fk
    # Validamos si el documento tiene recargo de equivalencia o no.
    tas_data = (
        db.query(tas.tas_tax, tas.tas_applyrate2).filter(tas.tas_id == n_tas).first()
    )
    if tas_data is not None:
        n_tas_tax = tas_data.tas_tax
        b_tas_apply_rate2 = tas_data.tas_applyrate2

    # Calculamos la tarifa del cliente (En caso de tener)
    price_list_data = db.query(cus).filter(order.cus_doh_fk == cus.cus_id).first()
    if price_list_data:
        n_plc_cus_fk = price_list_data.plc_cus_fk

    # Validamos los decimales del totalamount. Esto se realizará según la divisa del documento.
    # Por defecto pondremos 2.
    cur_data = db.query(cur.cur_decimals).filter(cur.cur_id == n_cur_doh_fk).first()
    if cur_data is not None:
        n_decimal_totalamount = cur_data.cur_decimals

    for line in lines:

        # Declaro las variables que me interesan que se inicialicen en el bucle.
        n_dli_id: int
        s_ite_id: str
        s_description: str
        x_quantity: Decimal | None = None
        x_quantity2: Decimal | None = None
        n_uom_stock: int
        n_uom_dli_fk: int
        n_uom_dli_fk2: int
        n_operation: int
        x_factor: Decimal | None = None
        n_decimal_cantidad: int
        n_decimal_cantidad2: int
        n_decimal_price: int
        n_decimal_price2: int
        n_decimal_cost: int
        n_decimal_cost2: int
        nIdcIte: int = 0
        # 2026-08-28 Comentado.
        # nDioIte1: int = 0
        # nDioIte2: int = 0
        nIdcID: int | None = None
        n_idc_dim1: int | None = None
        s_idc_dim_value1: str | None = None
        n_idc_dim2: int | None = None
        s_idc_dim_value2: str | None = None
        b_sale: bool
        b_variable: bool
        n_tat_ite_fk: int
        n_tat_ite_fk2: int
        s_uom_2_symbol: str
        x_item_price: Decimal = 0
        x_item_price2: Decimal = 0
        x_item_cost_price: Decimal = 0
        x_item_cost_price2: Decimal = 0
        x_weight_per_piece: Decimal = 0
        x_quantity_to_insert: Decimal = 0
        x_quantity_to_insert2: Decimal = 0
        x_price_to_insert: Decimal = 0
        x_price_to_insert2: Decimal = 0
        x_cost_to_insert: Decimal = 0
        x_cost_to_insert2: Decimal = 0
        x_importe_linea: Decimal = 0

        new_line = dli()

        # Primero obtengo el primer valor.
        n_dli_id = db.execute(text("SELECT nextval('DOCLINE_DLI_DLI_ID')")).scalar_one()

        # Se valida la existencia del artículo en la base de datos.
        s_ite_id = line.referenciaProducto
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
                ite.ite_id == s_ite_id,
                ite.ite_discontinued.is_(False),
                ite.ite_locked.is_(False),
            )
            .first()
        )
        if item_query is None:
            raise ValueError(f"Item: '{s_ite_id}' not found")
        else:
            s_description = item_query.ite_name
            n_decimal_cantidad = item_query.ite_decimalunit
            n_decimal_cantidad2 = item_query.ite_decimalunit
            n_decimal_price = item_query.ite_decimalsale
            n_decimal_price2 = item_query.ite_decimalsale
            n_decimal_cost = item_query.ite_decimalpurchase
            n_decimal_cost2 = item_query.ite_decimalpurchase
            b_sale = item_query.ite_sale
            b_variable = item_query.ite_variable
            n_uom_stock = item_query.uom_ite_fk
            # Se agrega idc a la consulta, para simplemente saber si el artículo tiene combinaciones.
            nIdcIte = item_query.idc_id
            # nDioIte1 = item_query.dio_ite_fk
            # nDioIte2 = item_query.dit_ite_fk
            n_tat_ite_fk = item_query.tat_ite_fk
            n_tat_ite_fk2 = item_query.tat_ite_fk2
            x_weight_per_piece = item_query.ite_weight
            n_uom_variable = item_query.uom_ite_fk5

        # Antes de seguir valido que el artículo se vende. En caso contrario, continuo con el siguiente.
        if b_sale is False:
            continue

        ttv_data = db.query(ttv.ttv_rate, ttv.ttv_rate2)
        match n_tas_tax:
            case 1:
                ttv_data = (
                    ttv_data.filter(
                        ttv.tat_ttv_fk == n_tat_ite_fk,
                        or_(
                            ttv.ttv_date >= s_doh_date,
                            ttv.ttv_date.is_(None),
                        ),
                    )
                    .order_by(ttv.ttv_id.asc())
                    .first()
                )
                if ttv_data is not None:
                    xTtvRate1 = ttv_data.ttv_rate
                    xTtvRate2 = ttv_data.ttv_rate2
                    nTatDliFkAux = n_tat_ite_fk
                    xLineTaxRate1 = xTtvRate1
                    if b_tas_apply_rate2 is True:
                        xLineTaxRate2 = xTtvRate2
                    else:
                        xLineTaxRate2 = 0
            case 2:
                ttv_data = (
                    ttv_data.filter(
                        ttv.tat_ttv_fk == n_tat_ite_fk2,
                        or_(
                            ttv.ttv_date >= s_doh_date,
                            ttv.ttv_date.is_(None),
                        ),
                    )
                    .order_by(ttv.ttv_id.asc())
                    .first()
                )
                if ttv_data is not None:
                    xTtvRate1 = ttv_data.ttv_rate
                    xTtvRate2 = ttv_data.ttv_rate2
                    nTatDliFkAux = n_tat_ite_fk2
                    xLineTaxRate1 = xTtvRate1
                    if b_tas_apply_rate2 is True:
                        xLineTaxRate2 = xTtvRate2
                    else:
                        xLineTaxRate2 = 0
            case 3:
                nTatDliFkAux = 1
                xLineTaxRate1 = 0
                xLineTaxRate2 = 0
        xLineTaxRate3 = x_irpf
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
                    idc.ite_idc_fk == s_ite_id,
                    idc.idc_default.is_(True),
                    idc.idc_discontinued.is_(False),
                ).first()

            print("idc_data ", idc_data)
            if idc_data is not None:
                nIdcID = idc_data.idc_id
                n_idc_dim1 = idc_data.idc_dimone
                s_idc_dim_value1 = idc_data.idc_dimonevalue
                n_idc_dim2 = idc_data.idc_dimtwo
                s_idc_dim_value2 = idc_data.idc_dimtwovalue
            else:
                raise ValueError(
                    f"Combination '{line.combination}' for item '{line.referenciaProducto}'"
                    f" doesn't exist'"
                )
        else:
            nIdcID = 0
            n_idc_dim1 = 0
            s_idc_dim_value1 = ""
            n_idc_dim2 = 0
            s_idc_dim_value2 = ""

        if line.cantidad:
            x_quantity = line.cantidad

        if line.formatoDeVenta:
            s_uom_2_symbol = line.formatoDeVenta
            # Antes de obtener los datos correspondientes a la conversión de unidades de medida. Vale la pena comprobar si se ha utilizado
            # la misma unidad de medida que la de stock.
            nUomParam = get_uom_id_by_symbol(db, s_uom_2_symbol)
            if nUomParam == 0:
                raise ValueError(f"Unit '{line.formatoDeVenta}' " f"doesn't exist'")
            else:
                # En caso de que obtengamos la misma unidad de stock que la del artículo. No realizamos ningún calculo.
                if nUomParam == n_uom_stock:
                    n_uom_dli_fk = n_uom_stock
                    n_uom_dli_fk2 = n_uom_stock
                    x_quantity2 = x_quantity
                else:
                    uom_data = get_item_uom_data(db, s_ite_id, s_uom_2_symbol)
                    if uom_data is not None:
                        n_uom_dli_fk = uom_data["uom_dli_fk"]
                        n_uom_dli_fk2 = uom_data["uom_dli_fk2"]
                        n_operation = uom_data["umo_operation"]
                        x_factor: Decimal = uom_data["umo_factor"]
                        n_decimal_cantidad2 = uom_data["uom_decimalunit"]

                        x_quantity2 = convert_quantity_to_stock(
                            x_quantity, n_operation, x_factor
                        )
                    else:
                        raise ValueError(
                            f"Unit '{line.formatoDeVenta}' "
                            f"not found for item '{s_ite_id}'"
                        )
        # Si no se nos pasan datos correspondinetes a unidades de medida, dejamos la unidad de stock del artículo.
        else:
            if b_variable is True:
                n_uom_dli_fk = n_uom_variable
                n_uom_dli_fk2 = n_uom_stock
            else:
                n_uom_dli_fk = n_uom_stock
                n_uom_dli_fk2 = n_uom_stock
                x_quantity2 = x_quantity
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
                    "price_list": n_plc_cus_fk,
                    "param5": 0,
                    "item_id": s_ite_id,
                    "item_dim_one": n_idc_dim1,
                    "item_dim_one_value": s_idc_dim_value1,
                    "item_dim_two": n_idc_dim2,
                    "item_dim_two_value": s_idc_dim_value2,
                    "batch_number": None,
                    "serial_number": None,
                    "expiration_date": None,
                    "item_uom": n_uom_dli_fk,
                },
            )
            .mappings()
            .first()
        )
        if prices_costs_data is None:
            raise ValueError(f"Prices and costs not found for item '{s_ite_id}'")

        x_item_price2 = prices_costs_data["price2"]
        x_item_cost_price2 = prices_costs_data["cost2"]
        x_item_price = prices_costs_data["price"]
        x_item_cost_price = prices_costs_data["cost"]

        # Si es de peso variable
        if b_variable is True:
            # En caso de que el usuario rellene el peso por pieza lo colocaremos aquí.
            if line.peso_pieza is not None:
                x_weight_per_piece = line.peso_pieza
            x_quantity_to_insert = x_quantity
            x_quantity_to_insert2 = x_quantity * x_weight_per_piece
            x_price_to_insert = x_item_price * x_weight_per_piece
            x_price_to_insert2 = x_item_price
            x_cost_to_insert = x_item_cost_price * x_weight_per_piece
            x_cost_to_insert2 = x_item_cost_price
            x_importe_linea = x_price_to_insert2 * x_quantity_to_insert2
        else:
            x_quantity_to_insert = x_quantity
            x_quantity_to_insert2 = x_quantity2
            x_price_to_insert = x_item_price
            x_price_to_insert2 = x_item_price2
            x_cost_to_insert = x_item_cost_price
            x_cost_to_insert2 = x_item_cost_price2
            x_importe_linea = x_item_price * x_quantity_to_insert

        new_line.dli_id = n_dli_id
        new_line.dli_order = n_order
        new_line.doh_dli_fk = n_doh_id
        new_line.ite_dli_fk = s_ite_id
        new_line.dli_description = s_description
        new_line.dli_descriptionchange = False
        new_line.dli_quantity = x_quantity_to_insert
        new_line.dli_quantity2 = x_quantity_to_insert2
        new_line.uom_dli_fk = n_uom_dli_fk
        new_line.war_dli_fk = n_war_dli_fk
        new_line.dli_price = x_price_to_insert
        new_line.dli_costprice = x_cost_to_insert
        new_line.uom_dli_fk2 = n_uom_dli_fk2
        new_line.dli_price2 = x_price_to_insert2
        new_line.dli_costprice2 = x_cost_to_insert2
        new_line.tat_dli_fk = nTatDliFkAux
        new_line.dli_taxrate1 = xLineTaxRate1
        new_line.dli_taxrate2 = xLineTaxRate2
        new_line.dli_taxrate3 = xLineTaxRate3
        new_line.dli_totalamount = x_importe_linea
        new_line.dli_decimalquantity = n_decimal_cantidad
        new_line.dli_decimalquantity2 = n_decimal_cantidad2
        new_line.dli_decimalprice = n_decimal_price
        new_line.dli_decimalprice2 = n_decimal_price2
        new_line.dli_decimalcost = n_decimal_cost
        new_line.dli_decimalcost2 = n_decimal_cost2
        new_line.dli_decimaltotalamount = n_decimal_totalamount
        new_line.dli_undelivered = x_quantity
        new_line.dli_delivered = 0
        new_line.idc_dli_fk = nIdcID
        new_line.dli_dimone = n_idc_dim1
        new_line.dli_dimonevalue = s_idc_dim_value1
        new_line.dli_dimtwo = n_idc_dim2
        new_line.dli_dimtwovalue = s_idc_dim_value2

        db.add(new_line)
        db.flush()

        db.refresh(new_line)

        # Aplicar luego.
        # # Una vez terminada la inserción debemos calcular las promociones. Esto se puede realizar con un función de base de datos existente.
        # # isql_Set_Calculate_Offers_In_Document
        calculate_offers_in_document(
            db=db,
            nMode=0,  # INSERCIÓN
            nIDDoc=n_doh_id,
            nPurchaseOrSale=2,
            nSupplierOrCustomer=int(n_cus_id),
            nDocumentType=2,
            sDateDocument=s_doh_date,
            nIDLine=n_dli_id,
            sItem=s_ite_id,
            nDimOne=n_idc_dim1,
            sDimOneValue=s_idc_dim_value1,
            nDimTwo=n_idc_dim2,
            sDimTwoValue=s_idc_dim_value2,
            sBatchNumber="",
            sSerialNumber="",
            sExpirationDate="2999-01-01",
            nQuantity=x_quantity_to_insert,
            nUM=n_uom_dli_fk,
            nQuantity2=x_quantity_to_insert2,
            nUM2=n_uom_dli_fk2,
            nPrice=x_price_to_insert,
            nPrice2=x_price_to_insert2,
            nCost=x_cost_to_insert,
            nCost2=x_cost_to_insert2,
            nDiscount1=0,
            nDiscount2=0,
            nDiscount3=0,
            nDecimalPrice=n_decimal_price,
            nDecimalPrice2=n_decimal_price2,
            nDecimalTotalAmount=n_decimal_totalamount,
            sRangeOffer="",
            nTaxRate1=xLineTaxRate1,
            nTaxRate2=xLineTaxRate2,
            nTaxRate3=xLineTaxRate3,
            nParent=0,
            sAuto=False,
            bLinesDocOrigin=False,
            bLinesDocDestiny=False,
            nDiscountCashUM=0,
        )
        if line.discounts is not None:
            calculate_manual_discounts(db, line.discounts, new_line)

        n_order += 1
    return True


def calculate_manual_discounts(db, line_discounts, new_line):
    # Para calcular los descuentos. Es necesario obtener los últimos datos de la línea insertada. Es por esto que realizamos un refresh de la misma.
    db.refresh(new_line)

    x_discount1: Decimal = 0
    x_discount2: Decimal = 0
    x_discount3: Decimal = 0
    x_discount_um: Decimal = 0
    x_discount: Decimal = 0
    x_total_discount: Decimal = 0
    s_discount1: str = ""
    s_discount2: str = ""
    s_discount3: str = ""
    s_discount_um: str = ""
    s_range_offer: str = ""

    # Valores por defecto obtenidos directamente de la línea insertada.
    x_price_to_insert: Decimal = new_line.dli_price
    x_price_to_insert2: Decimal = new_line.dli_price2
    x_quantity_to_insert: Decimal = new_line.dli_quantity
    # x_price : Decimal = new_line.dli_price
    x_total_amount_aux: Decimal = new_line.dli_totalamount
    n_decimal_total_amount: int = new_line.dli_decimaltotalamount
    x_total_amount_aux_copy: Decimal = x_total_amount_aux
    if line_discounts is not None:
        x_discount1 = line_discounts.dto1
        x_discount2 = line_discounts.dto2
        x_discount3 = line_discounts.dto3
        x_discount_um = line_discounts.dtoUM

        if x_discount1 is None or x_discount1 == 0:
            s_discount1 = "0"
        else:
            s_discount1 = f"*{x_discount1}"
        if x_discount2 is None or x_discount2 == 0:
            s_discount2 = "0"
        else:
            s_discount2 = f"*{x_discount2}"
        if x_discount3 is None or x_discount3 == 0:
            s_discount3 = "0"
        else:
            s_discount3 = f"*{x_discount3}"
        if x_discount_um is None or x_discount_um == 0:
            s_discount_um = "0"
        else:
            s_discount_um = f"*{x_discount_um}"
        if (
            s_discount1 != "0"
            or s_discount2 != "0"
            or s_discount3 != "0"
            or s_discount_um != "0"
        ):
            # Calculo el rangeOffer.
            s_range_offer = f"{x_price_to_insert};{x_price_to_insert2};{x_price_to_insert};{x_price_to_insert2};{s_discount1};{s_discount2};{s_discount3};{s_discount_um}"

            # Realizo cálculos por cada tipo de descuento.
            if x_discount_um is not None and x_discount_um != 0:
                # x_price = new_line.dli_price - x_discount_um
                x_discount = round(
                    x_quantity_to_insert * x_discount_um, n_decimal_total_amount
                )
                x_discount = round(
                    x_total_amount_aux - x_discount, n_decimal_total_amount
                )
                x_total_discount = x_total_discount + x_discount
                x_total_amount_aux = x_total_amount_aux - x_discount

            # Descuento 1
            if x_discount1 is not None and x_discount1 != 0:
                x_discount = x_total_amount_aux * x_discount1 / 100
                x_total_discount = x_total_discount + x_discount
                x_total_amount_aux = x_total_amount_aux - x_discount
            # Descuento 2 - En cascada.
            if x_discount2 is not None and x_discount2 != 0:
                x_discount = x_total_amount_aux * x_discount2 / 100
                x_total_discount = x_total_discount + x_discount
                x_total_amount_aux = x_total_amount_aux - x_discount
            # Descuento 3 - En cascada.
            if x_discount3 is not None and x_discount3 != 0:
                x_discount = x_total_amount_aux * x_discount3 / 100
                x_total_discount = x_total_discount + x_discount
                x_total_amount_aux = x_total_amount_aux - x_discount

            # Total
            x_total_amount_aux = x_total_amount_aux_copy - x_total_discount
            x_total_amount_aux_copy = round(
                x_total_amount_aux_copy, n_decimal_total_amount
            )

            # Cargamos cada uno de los descuentos calculados en la línea.
            new_line.dli_rangeoffer = s_range_offer
            new_line.dli_discount1 = x_discount1
            new_line.dli_discount2 = x_discount2
            new_line.dli_discount3 = x_discount3
            new_line.dli_discountcashunit = x_discount_um
            new_line.dli_discount = x_total_discount
            new_line.dli_totalamount = x_total_amount_aux_copy
            # Flush para que se guarden los cambios en la base de datos.
            db.flush()


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
