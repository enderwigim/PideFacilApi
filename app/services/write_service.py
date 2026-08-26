from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import func, text
from sqlalchemy.orm import Session, aliased

from app.db.models import (
    Address,
    Company,
    Customer,
    DocHeader,
    DocLine,
    DocumentSequence,
    Item,
    UnitOfMeasure,
    UnitOfMeasureCategory,
    UnitOfMeasureConversion,
)
from app.schemas.order_creation import CreationLineSchema, OrderCreationSchema


def create_order(db: Session, order: OrderCreationSchema):
    new_order = create_order_header(db=db, order=order)
    create_order_lines(db=db, lines=order.lineas, nDohID=new_order.doh_id)
    db.commit()
    return {"orderId": new_order.doh_id, "seqnumber": new_order.doh_seqnumber}


def create_order_lines(db: Session, lines: list[CreationLineSchema], order: DocHeader):
    nDohID: int
    nDliID: int
    nOrder: int
    sIteID: str
    sDescription: str
    xQuantity: Decimal
    xQuantity2: Decimal
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
    bSale: bool
    bVariable: bool
    nPlcCusFk: int | None = None

    sUom2Symbol: str

    nDohID = order.doh_id
    nWarDliFk = order.war_doh_fk

    for line in lines:
        new_line = DocLine()

        nDliID = db.execute(text("SELECT nextval('DOCLINE_DLI_DLI_ID')")).scalar_one()

        nOrder = db.query(func.max(DocLine.dli_order)).scalar()
        if nOrder is None:
            nOrder = 1
        else:
            nOrder += 1

        # Se valida la existencia del artículo en la base de datos.
        sIteID = line.referenciaProducto
        item_query = db.query(Item).filter(Item.ite_id == sIteID).first()
        if item_query is None:
            raise ValueError(f"Item: '{sIteID}' not found")
        else:
            sDescription = item_query.ite_name
            nDecimalCantidad = item_query.ite_decimalunit
            # nDecimalCantidad2: int
            nDecimalPrice = item_query.ite_decimalsale
            # nDecimalPrice2: int
            nDecimalCost = item_query.ite_decimalpurchase
            # nDecimalCost2: int
            bSale = item_query.ite_sale
            bVariable = item_query.ite_variable
            nUomStock = item_query.uom_ite_fk

        # Calculamos la tarifa del cliente (En caso de tener)
        price_list_data = (
            db.query(Customer).filter(order.cus_doh_fk == Customer.cus_id).first()
        )
        if price_list_data:
            nPlcCusFk = price_list_data.plc_cus_fk

        if line.cantidad:
            xQuantity = line.cantidad

        if line.formatoDeVenta:
            sUom2Symbol = line.formatoDeVenta
            uom_data = get_item_uom_data(db, sIteID, sUom2Symbol)
            if uom_data is not None:
                nUomDliFk = uom_data["uom_dli_fk"]
                nUomDliFk2 = uom_data["uom_dli_fk2"]
                nOperation = uom_data["umo_operation"]
                xFactor: Decimal = uom_data["umo_factor"]

                xQuantity2 = convert_quantity_to_stock(xQuantity, nOperation, xFactor)

        if bVariable is True:
            xWeightPerPiece = xQuantity2 / xQuantity

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
                    "item_dim_one": None,
                    "item_dim_one_value": None,
                    "item_dim_two": None,
                    "item_dim_two_value": None,
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

        new_line.dli_id = nDliID
        new_line.dli_order = nOrder
        new_line.doh_dli_fk = nDohID
        new_line.ite_dli_fk = sIteID
        new_line.dli_description = sDescription
        new_line.dli_descriptionchange = False
        new_line.uom_dli_fk = nUomDliFk
        new_line.uom_dli_fk2 = nUomDliFk2
        new_line.dli_quantity = xQuantity
        new_line.dli_quantity2 = xQuantity2
        new_line.war_dli_fk = nWarDliFk


def get_item_uom_data(
    db: Session,
    item_id: str,
    uom_symbol: str,
):
    UomStock = aliased(UnitOfMeasure)
    UomConversion = aliased(UnitOfMeasure)

    result = (
        db.query(
            UnitOfMeasureCategory.uom_umc_fk.label("uom_dli_fk"),
            UnitOfMeasureConversion.uom_umo_fk2.label("uom_dli_fk2"),
            UnitOfMeasureConversion.umo_operation.label("umo_operation"),
            UnitOfMeasureConversion.umo_factor.label("umo_factor"),
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
            Item.ite_id == item_id,
            UomConversion.uom_symbol == uom_symbol,
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
