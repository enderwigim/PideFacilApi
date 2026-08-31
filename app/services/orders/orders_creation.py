from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.models import Company, add, bra, cus, doh, seq
from app.schemas.orders.requests import OrderCreationSchema
from app.services.orders.line_creation import create_order_lines


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


def create_order_header(db: Session, order: OrderCreationSchema) -> doh:
    try:
        new_order = doh()
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
        customer_data = db.query(cus).filter(cus.cus_id == sCusId).first()
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
            db.query(add)
            .filter(add.cus_add_fk == sCusId, add.add_invoice.is_(True))
            .limit(1)
        ).first()
        if invoice_address_data is not None:
            nAddDoh = invoice_address_data.add_id
        else:
            nAddDoh = None

        ship_address_data = (
            db.query(add)
            .filter(add.cus_add_fk == sCusId, add.add_ship.is_(True))
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

        if order.sucursal is not None:
            branch_data = (
                db.query(bra.bra_seqSalesOrder, bra.war_bra_fk)
                .filter(bra.bra_id == order.sucursal)
                .first()
            )
            if branch_data is not None:
                sSequenceByDefault = branch_data.bra_seqSalesOrder
                nWarehouseByDefault = branch_data.war_bra_fk

        document_sequence_data = (
            db.query(seq)
            .filter(
                seq.seq_prefix.ilike(sSequenceByDefault),
                seq.seq_active.is_(True),
                seq.seq_type == nDocType,
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
