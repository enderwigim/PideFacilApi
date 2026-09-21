from collections.abc import Generator
from typing import Annotated

from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

# Engine de la base de datos central.
config_engine = create_engine(
    settings.config_database_url,
    pool_pre_ping=True,
    echo=settings.debug,
)


# SessionMaker de la base de datos central.
ConfigSessionLocal = sessionmaker(
    bind=config_engine,
    autoflush=False,
    autocommit=False,
)


# Dependencia para obtener sesiones de configuración.
def get_config_db() -> Generator[Session, None, None]:

    db = ConfigSessionLocal()

    try:
        yield db

    finally:
        db.close()


ConfigDbSession = Annotated[
    Session,
    Depends(get_config_db),
]
