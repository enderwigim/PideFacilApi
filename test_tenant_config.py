# Ajustar las rutas si tus archivos tienen
# nombres diferentes.


import sys

from sqlalchemy import select

from app.db.config_database import ConfigSessionLocal
from app.db.config_models import TenantAPIKeyModel
from app.security.api_key_service import create_tenant_api_key


def test_api_key(tenant_id: str):

    # Abrimos una sesión de la base de datos de configuración.
    with ConfigSessionLocal() as db:

        # Comprobamos si el Tenant ya tiene una API Key.
        existing_key = db.scalar(
            select(TenantAPIKeyModel).where(TenantAPIKeyModel.ten_tak_fk == tenant_id)
        )

        if existing_key is not None:
            print(f"El Tenant '{tenant_id}' ya tiene una API Key.")
            return

        # Generamos y almacenamos las credenciales.
        generated = create_tenant_api_key(
            db=db,
            tenant_id=tenant_id,
        )

        # Recuperamos el registro creado en PostgreSQL.
        saved_key = db.scalar(
            select(TenantAPIKeyModel).where(TenantAPIKeyModel.ten_tak_fk == tenant_id)
        )

        if saved_key is None:
            print("ERROR: No se ha encontrado la API Key.")
            return

        # Comprobamos que los valores almacenados
        # coinciden con los generados.
        key_matches = saved_key.tak_key == generated.s_api_key

        secret_matches = saved_key.tak_secret == generated.s_secret

        # Comprobamos la longitud de las credenciales.
        key_length_valid = len(saved_key.tak_key) == 32

        secret_length_valid = len(saved_key.tak_secret) == 32

        # Mostramos los resultados.
        print("\n--- RESULTADO DE LA PRUEBA ---")

        print("Tenant:", saved_key.ten_tak_fk)

        print("ID:", saved_key.tak_id)

        print("API Key guardada correctamente:", key_matches)

        print("Secret guardado correctamente:", secret_matches)

        print("Longitud API Key correcta:", key_length_valid)

        print("Longitud Secret correcta:", secret_length_valid)

        print("Credencial habilitada:", saved_key.tak_enabled)

        print("\n--- CREDENCIALES GENERADAS ---")

        print("API Key:", generated.s_api_key)

        print("Secret:", generated.s_secret)


if __name__ == "__main__":

    # Tenant por defecto.
    tenant_id = "cliente-a"

    # Permite especificar otro Tenant por consola.
    if len(sys.argv) > 1:
        tenant_id = sys.argv[1]

    test_api_key(tenant_id)
