from fastapi import Request

from app.core.tenancy.tenant import Tenant

TENANTS = {
    "cliente-a.apiiqs.local": Tenant(
        id="cliente-a",
        hostname="cliente-a.apiiqs.local",
        name="Cliente A",
    ),
    "cliente-b.apiiqs.local": Tenant(
        id="cliente-b",
        hostname="cliente-b.apiiqs.local",
        name="Cliente B",
    ),
}


# Obtengo el tenant a partir del hostname obtenido en la ruta.
def resolve_tenant(request: Request) -> Tenant:
    host = request.url.hostname
    tenant = TENANTS.get(host)

    if tenant is None:
        raise ValueError("Tenant no reconocido")

    return tenant
