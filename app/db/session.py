from collections.abc import Generator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.tenancy.registry import get_tenant_configuration
from app.core.tenancy.resolver import resolve_tenant
from app.core.tenancy.tenant import Tenant
from app.db.tenant_connection_manager import tenant_connection_manager
from app.db.tenant_database_context import TenantDatabaseContext

TenantDependency = Annotated[
    Tenant,
    Depends(resolve_tenant),
]


def get_tenant_database_context(
    tenant: TenantDependency,
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
