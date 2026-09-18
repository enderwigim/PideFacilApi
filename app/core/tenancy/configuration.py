from dataclasses import dataclass


@dataclass(frozen=True)
class TenantDatabaseConfiguration:
    database_url: str
    pool_pre_ping: bool = True
    echo: bool = False


@dataclass(frozen=True)
class TenantConfiguration:
    tenant_id: str
    enabled: bool
    database: TenantDatabaseConfiguration
