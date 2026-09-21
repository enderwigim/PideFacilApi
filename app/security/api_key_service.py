# Este servicio se encargará de la creación y validación de las API Key por Tenant.


from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.config_models import TenantAPIKeyModel, TenantModel
from app.security.api_key import GeneratedAPIKey, generate_api_key


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
