from fastapi import HTTPException
from sqlalchemy.engine import URL

from app.core.config import settings
from app.core.tenancy.configuration import (
    TenantConfiguration,
    TenantDatabaseConfiguration,
)
from app.core.tenancy.tenant import Tenant
from app.db.config_database import ConfigSessionLocal
from app.db.config_models import TenantDatabaseModel

# 2026-09-21
# TENANT_CONFIGURATIONS = {
#     "cliente-a": TenantConfiguration(
#         tenant_id="cliente-a",
#         enabled=True,
#         database=TenantDatabaseConfiguration(
#             database_url=settings.cliente_a_database_url,
#             echo=settings.debug,
#         ),
#     ),
#     "cliente-b": TenantConfiguration(
#         tenant_id="cliente-b",
#         enabled=True,
#         database=TenantDatabaseConfiguration(
#             database_url=settings.cliente_b_database_url,
#             echo=settings.debug,
#         ),
#     ),
# }


# Obtenemos la configuración del tenant.
def get_tenant_configuration(
    tenant: Tenant,
) -> TenantConfiguration:
    s_db_host: str
    s_db_port: str
    s_db_name: str
    s_db_username: str
    s_password_reference: str
    s_ssl_mode: str
    s_ssl_root_cert: str

    with ConfigSessionLocal() as db:
        database_data = (
            db.query(TenantDatabaseModel)
            .filter(TenantDatabaseModel.ten_tdb_fk == tenant.id)
            .first()
        )

        if database_data is None:
            raise HTTPException(
                status_code=503,
                detail="No existe configuración de base de datos para este tenant.",
            )

        s_db_host = database_data.tdb_host
        s_db_port = database_data.tdb_port
        s_db_name = database_data.tdb_name
        s_db_username = database_data.tdb_username
        # 2026-09-21 Es necesario que la contraseña después la encriptemos y analicemos como lo haremos. de momento irá asi.
        s_password_reference = database_data.tdb_password_secret
        s_ssl_mode = database_data.tdb_sslmode
        s_ssl_root_cert = database_data.tdb_sslmode

    # Configuración de conexión PostgreSQL.
    query_parameters = {
        "sslmode": s_ssl_mode,
    }

    if s_ssl_root_cert is not None:
        query_parameters["sslrootcert"] = s_ssl_root_cert

    # Construimos la URL de conexión.
    database_url = URL.create(
        drivername="postgresql+psycopg2",
        username=s_db_username,
        password=s_password_reference,
        host=s_db_host,
        port=s_db_port,
        database=s_db_name,
        query=query_parameters,
    )

    # Devolvemos la configuración que ya utiliza nuestro manager.
    return TenantConfiguration(
        tenant_id=tenant.id,
        enabled=True,
        database=TenantDatabaseConfiguration(
            database_url=database_url.render_as_string(hide_password=False),
            pool_pre_ping=True,
            echo=settings.debug,
        ),
    )
    # 2026-09-21 Santi. Deprecated
    # # A partir de las configuraciones que tenemos, intentaremos obtener el tenant correspondiente. En un futuro será un consulta a base de datos.
    # configuration = TENANT_CONFIGURATIONS.get(tenant.id)

    # if configuration is None:
    #     raise ValueError(f"No existe configuración para el tenant '{tenant.id}'")

    # if not configuration.enabled:
    #     raise ValueError(f"El tenant '{tenant.id}' está deshabilitado")
    # # Retornamos la configuración encontrada.
    # return configuration
