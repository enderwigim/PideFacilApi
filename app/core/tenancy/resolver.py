from fastapi import HTTPException, Request

from app.core.tenancy.tenant import Tenant
from app.db.config_database import ConfigSessionLocal
from app.db.config_models import TenantModel

# TENANTS = {
#     "cliente-a.apiiqs.local": Tenant(
#         id="cliente-a",
#         hostname="cliente-a.apiiqs.local",
#         name="Cliente A",
#     ),
#     "cliente-b.apiiqs.local": Tenant(
#         id="cliente-b",
#         hostname="cliente-b.apiiqs.local",
#         name="Cliente B",
#     ),
# }


# Obtengo el tenant a partir del hostname obtenido en la ruta.
def resolve_tenant(request: Request) -> Tenant:
    host = request.url.hostname

    if host is None:
        raise HTTPException(
            status_code=400,
            detail="Hostname no válido.",
        )

    host = host.lower().rstrip(".")

    with ConfigSessionLocal() as db:

        tenant_data = db.scalars(
            db.query(TenantModel).filter(TenantModel.ten_hostname == host)
        ).first()

        # Comprobamos si existe el tenant.
        if tenant_data is None:
            raise HTTPException(
                status_code=404,
                detail="Tenant no reconocido.",
            )

        # Comprobamos si está habilitado.
        if not tenant_data.ten_enabled:
            raise HTTPException(
                status_code=403,
                detail="El tenant se encuentra deshabilitado.",
            )

        # Construimos nuestro objeto Tenant.
        return Tenant(
            id=tenant_data.ten_id,
            hostname=tenant_data.ten_hostname,
            name=tenant_data.ten_name,
        )

    # host = request.url.hostname
    # tenant = TENANTS.get(host)

    # if tenant is None:
    #     raise ValueError("Tenant no reconocido")

    # return tenant
