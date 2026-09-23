# Este servicio se encargará de la creación y validación de las API Key por Tenant.


import hmac
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.config_database import ConfigSessionLocal
from app.db.config_models import TenantAPIKeyModel, TenantModel
from app.exceptions.security import *
from app.security.api_key import (
    GeneratedAPIKey,
    generate_api_key,
    get_signature,
)


def create_tenant_api_key(
    db: Session,
    tenant_id: str,
) -> GeneratedAPIKey:
    # Declaramos variables
    generated_api_key: GeneratedAPIKey
    api_key_record: TenantAPIKeyModel
    tenant: any

    # Coprobamos que el tenant existe.
    tenant = db.scalar(
        select(TenantModel.ten_id).where(TenantModel.ten_id == tenant_id)
    )

    if tenant is None:
        # Dar error por no encontrar el tenant.
        raise ValueError("El Tenant no existe o está deshabilitado.")

    # Generamos la api_key
    generated_api_key = generate_api_key()

    # Generamos el modelo que insertaremos en la base de datos.
    api_key_record = TenantAPIKeyModel(
        ten_tak_fk=tenant_id,
        tak_key=generated_api_key.s_api_key,
        tak_secret=generated_api_key.s_secret,
    )

    # Insertamos en la base de datos.
    try:
        db.add(api_key_record)
        db.commit()

    except Exception:
        db.rollback()
        raise

    return generated_api_key


def get_aunthenticated_tenant(s_api_key, s_signature, s_timestamp, tenant_id) -> bool:
    # tu_parsed: tuple | None = None
    # s_key_prefix: str
    # s_secret: str
    dt_now: datetime
    s_our_signature: str
    b_valid_signature: bool

    if s_api_key is None:
        raise ApiKeyRequired()

    if s_signature is None:
        raise SignatureRequired()
        # Generar error para signature.
    if s_timestamp is None:
        raise DateTimeRequired()
        # Generar error para timestamp

    try:
        dt_timestamp = datetime.strptime(
            s_timestamp,
            "%Y-%m-%dT%H:%M:%SZ",
        ).replace(tzinfo=timezone.utc)
    except ValueError:
        raise TimestampInvalidFormat()

    # Obsoleto.
    # Se separa el identificador
    # tu_parsed = parse_api_key(api_key=s_api_key)

    # if tu_parsed is None:
    #     raise ApiKeyInvalidFormat()
    dt_now = datetime.now(timezone.utc)
    # s_now = dt_now.strftime("%Y-%m-%dT%H:%M:%SZ")
    # Obtenemos el secret para el tenant especifico.
    with ConfigSessionLocal() as db:

        # Buscamos la API Key mediante su identificador y su tenant.
        saved_data = db.execute(
            select(
                TenantAPIKeyModel.tak_key,
                TenantAPIKeyModel.tak_secret,
            )
            .join(
                TenantModel,
                TenantAPIKeyModel.ten_tak_fk == TenantModel.ten_id,
            )
            .where(
                # Tenant solicitado.
                TenantAPIKeyModel.ten_tak_fk == tenant_id,
                # API Key habilitada.
                TenantAPIKeyModel.tak_enabled.is_(True),
                # API Key no caducada.
                # or_(
                #     TenantAPIKeyModel.tak_expiresat.is_(None),
                #     TenantAPIKeyModel.tak_expiresat > dt_now,
                # ),
                # Tenant habilitado.
                TenantModel.ten_enabled.is_(True),
            )
        ).first()

        # Validamos que hayamos encontrado algo.
        if saved_data is None:
            raise ApiKeyNotFound()

        # Comenzamos a construir las validaciones.
        if saved_data.tak_key != s_api_key:
            raise ApiKeyRequired()

        # Rechazamos timestamps futuros o con más de 5 minutos de antigüedad.
        if not (dt_now - timedelta(minutes=5) <= dt_timestamp <= dt_now):
            raise DateTimeExpired()

        # Validamos el signature:
        s_our_signature = get_signature(
            s_api_key=s_api_key, s_timestamp=s_timestamp, s_secret=saved_data.tak_secret
        )

        b_valid_signature = _verify_signature(
            s_our_signature=s_our_signature, s_received_signature=s_signature
        )
        if b_valid_signature is False:
            raise SignatureMismatch()

            # Generar error de signature.
        return True
        # Comprobamos el secreto.
        # is_valid = verify_api_key(
        #     secret=s_secret,
        #     stored_hash=saved_key.tak_key_hash,
        # )


def _verify_signature(
    s_our_signature: str,
    s_received_signature: str,
) -> bool:
    return hmac.compare_digest(
        s_our_signature,
        s_received_signature,
    )
