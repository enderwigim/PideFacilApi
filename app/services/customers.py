from sqlalchemy.orm import Session

from app.api.v1.schemas.customers.responses import CustomerSchema
from app.db.tenant_models import TenantModels
from app.exceptions.customer import CustomerNotActiveError, CustomerNotFoundError


# Primero se obtienen los clientes, luego se obtienen cada uno de los telefonos disponibles, tanto
# de contactos como de direcciones.
# Luego se organizan los telefonos para que incluya primero los de los contactos, y en caso de que aún quede espacio (Hasta 3)
# se incluirán los de las direcciones.
def get_customers(db: Session, models: TenantModels) -> list[CustomerSchema]:
    add = models.add
    con = models.con
    cus = models.cus
    customer_data = (
        db.query(
            cus.cus_id,
            cus.cus_active,
            add.add_phone1,
            add.add_phone2,
            con.con_phone1,
            con.con_phone2,
        )
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

    if len(result) == 0:
        raise CustomerNotFoundError(referencia="Todos los clientes")
    return result


# Primero se obtienen los clientes, luego se obtienen cada uno de los telefonos disponibles, tanto
# de contactos como de direcciones.
# Luego se organizan los telefonos para que incluya primero los de los contactos, y en caso de que aún quede espacio (Hasta 3)
# se incluirán los de las direcciones.
def get_customer_by_id(
    db: Session, customer_id: int, models: TenantModels
) -> CustomerSchema:
    add = models.add
    con = models.con
    cus = models.cus
    customer_data = (
        db.query(
            cus.cus_id,
            cus.cus_active,
            add.add_phone1,
            add.add_phone2,
            con.con_phone1,
            con.con_phone2,
        )
        .outerjoin(con, (cus.cus_id == con.cus_con_fk))
        .outerjoin(add, (cus.cus_id == add.cus_add_fk))
        .order_by(cus.cus_id.asc(), add.add_invoice.desc(), con.con_id.asc())
        .filter(cus.cus_id == customer_id)
        .first()
    )
    if customer_data is None:
        raise CustomerNotFoundError(referencia=str(customer_id))

    customer, address, contact = customer_data

    s_reference = str(customer.cus_id)
    s_name = customer.cus_corporatename
    arr_contact_phones = []
    arr_address_phones = []
    b_active = customer.cus_active

    if not b_active:
        raise CustomerNotActiveError(referencia=s_reference)

    if contact is not None:
        for phone in (contact.con_phone1, contact.con_phone2):
            if phone is not None and phone not in arr_contact_phones:
                arr_contact_phones.append(phone)
    if address is not None:
        for phone in (address.add_phone1, address.add_phone2):
            if phone is not None and phone not in arr_address_phones:
                arr_address_phones.append(phone)
    # Loopeamos por el resultado filtrando los telefonos correspondientes.
    # result: list[CustomerSchema] = []

    # Se agregan los primeros 3 telefonos en contactos.
    phones = arr_contact_phones[:3]
    # Si todavía no se llega a 3. Agrego telefonos hasta 3.
    if len(phones) < 3:
        for phone in arr_address_phones:
            if phone not in phones:
                phones.append(phone)

            if len(phones) == 3:
                break

    result_customer = CustomerSchema(
        referencia=s_reference,
        nombre=s_name,
        telefonos=phones,
    )

    return result_customer
