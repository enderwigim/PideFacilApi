from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from app.db.tenant_models import TenantModels


@dataclass
class TenantDatabaseContext:
    engine: Engine
    session_maker: sessionmaker
    base: Any
    models: TenantModels
    analysis_version: int
    last_version_check: datetime
