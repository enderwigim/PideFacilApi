from collections.abc import Generator
from typing import Annotated

from fastapi import Depends
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session

from app.core.tenancy.registry import get_tenant_configuration
from app.core.tenancy.resolver import resolve_tenant
from app.core.tenancy.tenant import Tenant
from app.db.tenant_connection_manager import tenant_connection_manager
from app.db.tenant_database_context import TenantDatabaseContext
from app.exceptions.security import ApiKeyInvalidFormat
from app.security.api_key_service import get_aunthenticated_tenant

api_key_header = APIKeyHeader(
    name="X-API-Key",
    auto_error=False,
    scheme_name="TenantAPIKey",
)

TenantDependency = Annotated[
    Tenant,
    Depends(resolve_tenant),
]


def authenticate_tenant(
    tenant: TenantDependency,
    api_key: Annotated[
        str | None,
        Depends(api_key_header),
    ],
) -> Tenant:

    # Validamos la API Key para el Tenant solicitado.
    is_authenticated = get_aunthenticated_tenant(
        s_api_key=api_key,
        tenant_id=tenant.id,
    )

    # Si la API Key no es válida, rechazamos la petición.
    if not is_authenticated:
        raise ApiKeyInvalidFormat()

    # Si es válida, devolvemos el Tenant autenticado.
    return tenant


AuthenticatedTenantDependency = Annotated[
    Tenant,
    Depends(authenticate_tenant),
]


def get_tenant_database_context(
    tenant: AuthenticatedTenantDependency,
) -> TenantDatabaseContext:

    configuration = get_tenant_configuration(tenant)

    return tenant_connection_manager.get_context(configuration)


TenantDbContext = Annotated[
    TenantDatabaseContext,
    Depends(get_tenant_database_context),
]


def get_db(
    context: TenantDbContext,
) -> Generator[Session, None, None]:

    db = context.session_maker()

    try:
        yield db
    finally:
        db.close()


DbSession = Annotated[
    Session,
    Depends(get_db),
]
