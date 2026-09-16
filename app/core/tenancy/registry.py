from app.core.config import settings
from app.core.tenancy.configuration import (
    TenantConfiguration,
    TenantDatabaseConfiguration,
)
from app.core.tenancy.tenant import Tenant

TENANT_CONFIGURATIONS = {
    "cliente-a": TenantConfiguration(
        tenant_id="cliente-a",
        enabled=True,
        database=TenantDatabaseConfiguration(
            database_url=settings.cliente_a_database_url,
            echo=settings.debug,
        ),
    ),
    "cliente-b": TenantConfiguration(
        tenant_id="cliente-b",
        enabled=True,
        database=TenantDatabaseConfiguration(
            database_url=settings.cliente_b_database_url,
            echo=settings.debug,
        ),
    ),
}


# Obtenemos la configuración del tenant.
def get_tenant_configuration(
    tenant: Tenant,
) -> TenantConfiguration:
    # A partir de las configuraciones que tenemos, intentaremos obtener el tenant correspondiente. En un futuro será un consulta a base de datos.
    configuration = TENANT_CONFIGURATIONS.get(tenant.id)

    if configuration is None:
        raise ValueError(f"No existe configuración para el tenant '{tenant.id}'")

    if not configuration.enabled:
        raise ValueError(f"El tenant '{tenant.id}' está deshabilitado")
    # Retornamos la configuración encontrada.
    return configuration
