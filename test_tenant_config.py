from sqlalchemy import select

from app.db.config_database import ConfigSessionLocal
from app.db.config_models import (
    TenantAPIKeyModel,
    TenantModel,
)
from app.security.api_key import (
    generate_api_key,
    verify_api_key,
)


def test_api_key():

    # Conexión a nuestra base de datos de configuración.
    with ConfigSessionLocal() as db:

        # Buscamos el Tenant.
        tenant = db.scalar(
            select(TenantModel).where(
                TenantModel.ten_id == "cliente-a",
                TenantModel.ten_enabled.is_(True),
            )
        )

        if tenant is None:
            print("El Tenant no existe o está deshabilitado.")
            return

        # Generamos la API Key.
        generated = generate_api_key()

        # Preparamos el registro.
        api_key_record = TenantAPIKeyModel(
            tak_id=generated.key_id,
            ten_tak_fk=tenant.ten_id,
            tak_name="PideFácil - Prueba",
            tak_key_prefix=generated.key_prefix,
            tak_key_hash=generated.key_hash,
            tak_enabled=True,
        )

        # Guardamos el registro en la base administrativa.
        try:
            db.add(api_key_record)
            db.commit()

        except Exception:
            db.rollback()
            raise

        # Recuperamos el registro guardado.
        saved_key = db.scalar(
            select(TenantAPIKeyModel).where(
                TenantAPIKeyModel.tak_id == generated.key_id,
            )
        )

        if saved_key is None:
            print("ERROR: No se ha guardado la API Key.")
            return

        # Extraemos el secreto para comprobar su hash.
        prefix = f"iqs_live_{generated.key_prefix}_"

        secret = generated.api_key.removeprefix(prefix)

        is_valid = verify_api_key(
            secret=secret,
            stored_hash=saved_key.tak_key_hash,
        )

        print("\n--- API KEY GUARDADA ---")

        print("Tenant:", saved_key.ten_tak_fk)
        print("Integración:", saved_key.tak_name)
        print("ID:", saved_key.tak_id)
        print("API Key válida:", is_valid)

        # Solo para esta prueba local.
        print("\nAPI KEY COMPLETA:")
        print(generated.api_key)


if __name__ == "__main__":
    test_api_key()
