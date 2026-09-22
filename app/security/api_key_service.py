# Este servicio se encargará de la creación y validación de las API Key por Tenant.


from datetime import datetime, timezone

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.db.config_database import ConfigSessionLocal
from app.db.config_models import TenantAPIKeyModel, TenantModel
from app.exceptions.security import *
from app.security.api_key import (
    GeneratedAPIKey,
    generate_api_key,
    parse_api_key,
    verify_api_key,
)


def create_tenant_api_key(
    db: Session,
    tenant_id: str,
    key_name: str,
    expires_at: datetime | None = None,
) -> GeneratedAPIKey:

    # Coprobamos que el tenant existe.
    tenant = db.scalar(
        select(TenantModel.ten_id).where(TenantModel.ten_id == tenant_id)
    ).first()

    if tenant is None:
        # Dar error por no encontrar el tenant.
        raise ValueError("El Tenant no existe o está deshabilitado.")

    # Validamos el nombre de la clave a generar.
    key_name = key_name.strip()
    if key_name is None or len(key_name) > 150:
        raise ValueError("El nombre de la integración no es válido.")

    if expires_at is not None:
        if expires_at.tzinfo is None:
            raise ValueError("La fecha de caducidad debe incluir zona horaria.")
        if expires_at <= datetime.now(timezone.utc):
            raise ValueError("La fecha de caducidad debe ser futura.")

    generated_api_key = generate_api_key()

    api_key_record = TenantAPIKeyModel(
        tak_id=generated_api_key.key_id,
        ten_tak_fk=tenant_id,
        tak_name=key_name,
        tak_key_prefix=generated_api_key.key_prefix,
        tak_key_hash=generated_api_key.key_hash,
        tak_enabled=True,
        tak_expires_at=expires_at,
    )

    # 6. Guardar la credencial.
    try:

        db.add(api_key_record)

        db.commit()

    except Exception:

        db.rollback()

        raise

    # 7. Devolver la credencial completa.
    return generated_api_key


def get_aunthenticated_tenant(s_api_key, tenant_id) -> bool:
    tu_parsed: tuple | None = None
    s_key_prefix: str
    s_secret: str
    dt_now: datetime

    if s_api_key is None:
        raise ApiKeyRequired()

    # Se separa el identificador
    tu_parsed = parse_api_key(api_key=s_api_key)

    if tu_parsed is None:
        raise ApiKeyInvalidFormat()

    s_key_prefix, s_secret = tu_parsed

    with ConfigSessionLocal() as db:
        dt_now = datetime.now(timezone.utc)
        # Buscamos la API Key mediante su identificador y su tenant.
        saved_key = db.execute(
            select(
                TenantAPIKeyModel.tak_key_prefix,
                TenantAPIKeyModel.ten_tak_fk,
                TenantAPIKeyModel.tak_enabled,
                TenantAPIKeyModel.tak_revoked_at,
                TenantAPIKeyModel.tak_expires_at,
                TenantAPIKeyModel.tak_key_hash,
                TenantModel.ten_enabled,
            )
            .join(
                TenantModel,
                TenantAPIKeyModel.ten_tak_fk == TenantModel.ten_id,
            )
            .where(
                # Identificador de la credencial.
                TenantAPIKeyModel.tak_key_prefix == s_key_prefix,
                # Tenant solicitado.
                TenantAPIKeyModel.ten_tak_fk == tenant_id,
                # API Key habilitada.
                TenantAPIKeyModel.tak_enabled.is_(True),
                # API Key no revocada.
                TenantAPIKeyModel.tak_revoked_at.is_(None),
                # API Key no caducada.
                or_(
                    TenantAPIKeyModel.tak_expires_at.is_(None),
                    TenantAPIKeyModel.tak_expires_at > dt_now,
                ),
                # Tenant habilitado.
                TenantModel.ten_enabled.is_(True),
            )
        ).first()

        if saved_key is None:
            raise ApiKeyNotFound()

        # Comprobamos el secreto.

        is_valid = verify_api_key(
            secret=s_secret,
            stored_hash=saved_key.tak_key_hash,
        )

        return is_valid
