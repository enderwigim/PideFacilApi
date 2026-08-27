from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import inspect, or_, text
from sqlalchemy.orm import Session, aliased

from app.db.models import (
    Address,
    Company,
    Customer,
    DocHeader,
    DocLine,
    DocumentSequence,
    Item,
    ItemDimCombination,
    UnitOfMeasure,
    UnitOfMeasureCategory,
    UnitOfMeasureConversion,
    tas,
    ttv,
)
from app.schemas.order_creation import CreationLineSchema, OrderCreationSchema


def create_order(db: Session, order: OrderCreationSchema):
    try:
        new_order = create_order_header(db=db, order=order)

        create_order_lines(db=db, lines=order.lineas, order=new_order)

        db.commit()

        return {
            "orderId": new_order.doh_id,
            "seqnumber": new_order.doh_seqnumber,
        }

    except Exception:
        db.rollback()
        raise


def create_order_lines(db: Session, lines: list[CreationLineSchema], order: DocHeader):

    mapper = inspect(DocLine)

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
    nDioIte1: int = 0
    nDioIte2: int = 0
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

    nOrder = 1
    nDohID = order.doh_id
    nWarDliFk = order.war_doh_fk
    nTas = order.tas_doh_fk
    sDohDate = order.doh_date
    xIRPF = order.doh_holdrate

    # Validamos si el documento tiene recargo de equivalencia o no.
    tas_data = (
        db.query(tas.tas_tax, tas.tas_applyrate2).filter(tas.tas_id == nTas).first()
    )
    if tas_data is not None:
        nTasTax = tas_data.tas_tax
        bTasApplyRate2 = tas_data.tas_applyrate2

    # Calculamos la tarifa del cliente (En caso de tener)
    price_list_data = (
        db.query(Customer).filter(order.cus_doh_fk == Customer.cus_id).first()
    )
    if price_list_data:
        nPlcCusFk = price_list_data.plc_cus_fk

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
        nDioIte1: int = 0
        nDioIte2: int = 0
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

        sUom2Symbol: str

        new_line = DocLine()

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
                Item.ite_name,
                Item.ite_decimalunit,
                Item.ite_decimalsale,
                Item.ite_decimalpurchase,
                Item.ite_sale,
                Item.ite_variable,
                Item.uom_ite_fk,
                Item.dio_ite_fk,
                Item.dit_ite_fk,
                Item.tat_ite_fk,
                Item.tat_ite_fk2,
                Item.ite_weight,
                Item.uom_ite_fk5,
            )
            .filter(
                Item.ite_id == sIteID,
                Item.ite_discontinued.is_(False),
                Item.ite_locked.is_(False),
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
            nDioIte1 = item_query.dio_ite_fk
            nDioIte2 = item_query.dit_ite_fk
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
        # Si el artículo tiene combinaciones, buscaremos las que tenga marcada por defecto. Esta será la que insertemos en el artículo.
        # Además, podría intentar ponerse algún str de referencia en la ruta, por si ellos quisieran ampliarlo y permitieran la especificación
        # de dicha combinación.
        print("nDioIte1 : ", nDioIte1)
        if nDioIte1 != 0 or nDioIte2 != 0:
            idc_data = (
                db.query(
                    ItemDimCombination.idc_id,
                    ItemDimCombination.idc_dimone,
                    ItemDimCombination.idc_dimonevalue,
                    ItemDimCombination.idc_dimtwo,
                    ItemDimCombination.idc_dimtwovalue,
                )
                .filter(
                    ItemDimCombination.ite_idc_fk == sIteID,
                    ItemDimCombination.idc_default.is_(True),
                    ItemDimCombination.idc_discontinued.is_(False),
                )
                .first()
            )
            print("idc_data ", idc_data)
            if idc_data is not None:
                nIdcID = idc_data.idc_id
                nIdcDim1 = idc_data.idc_dimone
                sIdcDimValue1 = idc_data.idc_dimonevalue
                nIdcDim2 = idc_data.idc_dimtwo
                sIdcDimValue2 = idc_data.idc_dimtwovalue
            else:
                nIdcDim1 = 0
                sIdcDimValue1 = ""
                nIdcDim2 = 0
                sIdcDimValue2 = ""
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
                    print("------ uom_data  ", uom_data)
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
            print("bVariable ", bVariable)
            if bVariable is True:
                nUomDliFk = nUomVariable
                nUomDliFk2 = nUomStock
                print("nUomDliFk ", nUomDliFk)
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
            print("xWeightPerPiece ", xWeightPerPiece)
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
        print("new_line.uom_dli_fk ", new_line.uom_dli_fk)
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
        # new_line.dli_decimaltotalamount
        new_line.dli_undelivered = xQuantity
        new_line.dli_delivered = 0
        # new_line.wab_dli_fk  NO NECESITO UBICACIONES EN PEDIDO.
        new_line.dli_rangeoffer = sRangeOffer
        # new_line.dli_weight // NECESITO???

        # Revisar Debería calcular los descuentos correspondientes con el articulo, cliente y condiciones de venta.
        new_line.dli_discountcashunit = 0
        new_line.dli_discount = 0
        print(nIdcDim1)
        new_line.idc_dli_fk = nIdcID
        new_line.dli_dimone = nIdcDim1
        new_line.dli_dimonevalue = sIdcDimValue1
        new_line.dli_dimtwo = nIdcDim2
        new_line.dli_dimtwovalue = sIdcDimValue2

        db.add(new_line)
        db.flush()

        db.refresh(new_line)

        nOrder += 1


def get_uom_id_by_symbol(db: Session, uom_symbol):
    # A partir de un simbolo nos devuelve el ID de la tabla UNITOFMEASURE_UOM. En caso de que dicho simbolo no se encuentre, devuelve 0.
    uom_data = (
        db.query(UnitOfMeasure.uom_id)
        .filter(UnitOfMeasure.uom_symbol.ilike(uom_symbol.strip()))
        .first()
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
    UomConversion = aliased(UnitOfMeasure)

    result = (
        db.query(
            UnitOfMeasureConversion.uom_umo_fk2.label("uom_dli_fk"),
            UnitOfMeasureCategory.uom_umc_fk.label("uom_dli_fk2"),
            UnitOfMeasureConversion.umo_operation.label("umo_operation"),
            UnitOfMeasureConversion.umo_factor.label("umo_factor"),
            UomConversion.uom_decimalunit.label("uom_decimalunit"),
        )
        # Le decimos explícitamente que ITEM_ITE es el FROM principal
        .select_from(Item)
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
            UomConversion,
            UnitOfMeasureConversion.uom_umo_fk2 == UomConversion.uom_id,
        )
        .filter(
            Item.ite_id == item_id, UomConversion.uom_symbol.ilike(uom_symbol.strip())
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


def create_order_header(db: Session, order: OrderCreationSchema) -> DocHeader:
    try:
        new_order = DocHeader()
        ## --- INSERCIÓN  VALORES PODER DEFECTO --- ##
        nDocType: int = 2  # La inserción de este documento siempre será de tipo 2.
        nIdDocument: int
        nWarehouseByDefault: int  # Almacén por defecto
        sSequenceByDefault: int  # Secuencia
        nSeqNumber: int  # Nº de documento
        sDate: str
        sTime: str
        # nPurchaseOrSale: int
        nCurDoh: int | None = None  # Divisa
        nPamDoh: int | None = None  # Forma de pago
        nAddDoh: int | None = None  # Dirección de facturación
        nAddDoh2: int | None = None  # Dirección de envío
        nAcoDoh: int | None = None  # Grupo de clientes de comisión
        nTcoDoh: int | None = None  # Empresa de transporte
        nTasType: int  # Sistema de impuestos
        sNotes: str  # Observaciones
        nDecimal: int  # Decimal
        bSp: bool = False  # Modo de acceso
        sCusId: str | None = None  # Código de cliente
        sSupId: str | None = None  # Código de proveedor
        xDiscount1: Decimal  # Descuentos de cabecera 1
        xDiscount2: Decimal  # Descuentos de cabecera 2
        xDiscount3: Decimal  # Descuentos de cabecera 3
        nPapId: int | None = None  # Punto de cobro por defecto
        nWarDohFk: int | None = None
        # nPaymentType: int
        nDecimal: int = 2  # Por defecto siempre 2

        # Como el tipo de documento es pedido de venta (nDocType = 2)
        # nPurchaseOrSale = 2
        sCusId = order.referenciaCliente
        sSupId = None

        # Obtenemos los datos del cliente.
        customer_data = db.query(Customer).filter(Customer.cus_id == sCusId).first()
        if customer_data is not None:
            nPamDoh = customer_data.pam_cus_fk
            nTasType = customer_data.tas_cus_fk
            nAcoDoh = customer_data.aco_cus_fk
            nTcoDoh = customer_data.tco_cus_fk
            xDiscount1 = customer_data.cus_disc1
            xDiscount2 = customer_data.cus_disc2
            xDiscount3 = customer_data.cus_disc3
            sNotes = customer_data.cus_notes
        else:
            raise ValueError(f"Customer: '{order.referenciaCliente}' not found")

        invoice_address_data = (
            db.query(Address)
            .filter(Address.cus_add_fk == sCusId, Address.add_invoice.is_(True))
            .limit(1)
        ).first()
        if invoice_address_data is not None:
            nAddDoh = invoice_address_data.add_id
        else:
            nAddDoh = None

        ship_address_data = (
            db.query(Address)
            .filter(Address.cus_add_fk == sCusId, Address.add_ship.is_(True))
            .limit(1)
        ).first()
        if ship_address_data is not None:
            nAddDoh2 = ship_address_data.add_id
        else:
            nAddDoh2 = None

        # Obtenemos datos provenientes de COMPANY_COM
        company_data = db.query(Company).first()
        if company_data is not None:
            sSequenceByDefault = company_data.com_seqsalesorder
            nWarehouseByDefault = company_data.war_com_fk
            nCurDoh = company_data.cur_com_fk
            nPapId = company_data.pap_com_fk
            nWarDohFk = company_data.war_com_fk
        else:
            raise ValueError("Company setup not found")

        document_sequence_data = (
            db.query(DocumentSequence)
            .filter(
                DocumentSequence.seq_prefix.ilike(sSequenceByDefault),
                DocumentSequence.seq_active.is_(True),
                DocumentSequence.seq_type == nDocType,
            )
            .first()
        )
        if document_sequence_data is not None:
            bSp = document_sequence_data.seq_sp
            nSeqNumber = document_sequence_data.seq_lastnumber + 1

        # Cálculamos la fecha de hoy. Aquí insertaremos el pedido.
        now = datetime.now(timezone.utc)
        sDate = now.date()
        sTime = now.time()
        sNotes = order.observaciones

        nIdDocument = db.execute(
            text("SELECT nextval('DOCHEADER_DOH_DOH_ID')")
        ).scalar_one()
        new_order.doh_id = nIdDocument

        # Campos mínimos a insertar:
        new_order.doh_type = nDocType
        new_order.doh_sp = bSp
        new_order.doh_sequence = sSequenceByDefault
        new_order.doh_number = nSeqNumber
        new_order.doh_date = sDate
        new_order.doh_time = sTime
        new_order.cur_doh_fk = nCurDoh
        new_order.pam_doh_fk = nPamDoh
        new_order.cus_doh_fk = sCusId
        new_order.sup_doh_fk = sSupId
        new_order.war_doh_fk = nWarehouseByDefault
        new_order.add_doh_fk = nAddDoh
        new_order.add_doh_fk2 = nAddDoh2
        new_order.aco_doh_fk = nAcoDoh
        new_order.tco_doh_fk = nTcoDoh
        new_order.doh_disc1 = xDiscount1
        new_order.doh_disc2 = xDiscount2
        new_order.doh_disc3 = xDiscount3
        new_order.tas_doh_fk = nTasType
        new_order.doh_notes = sNotes
        new_order.doh_decimal = nDecimal
        new_order.pap_doh_fk = nPapId
        new_order.doh_type = nDocType
        new_order.war_doh_fk = nWarDohFk

        if order.fechaEntrega is not None:
            new_order.doh_deliveryDateDoc = order.fechaEntrega

        db.add(new_order)
        db.flush()

        return new_order
    except Exception:
        db.rollback()
        raise
