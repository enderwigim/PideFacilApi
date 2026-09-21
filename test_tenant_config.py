from sqlalchemy.engine import make_url

from app.core.tenancy.registry import get_tenant_configuration
from app.core.tenancy.tenant import Tenant


def test_tenant(tenant_id: str):

    tenant = Tenant(
        id=tenant_id,
        hostname=f"{tenant_id}.apiiqs.local",
        name=tenant_id,
    )

    # Recuperamos la configuración desde la BD central.
    configuration = get_tenant_configuration(tenant)

    # Obtenemos los componentes de la URL.
    url = make_url(configuration.database.database_url)

    print(f"\n--- {tenant_id} ---")
    print(f"Tenant: {configuration.tenant_id}")
    print(f"Host BD: {url.host}")
    print(f"Puerto: {url.port}")
    print(f"Base de datos: {url.database}")


if __name__ == "__main__":
    test_tenant("cliente-a")
    test_tenant("cliente-b")
