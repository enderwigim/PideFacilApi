from sqlalchemy import MetaData, create_engine
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import sessionmaker
from tables import TABLES

from app.core.config import settings

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    echo=settings.debug,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)

metadata = MetaData()


metadata.reflect(
    bind=engine,
    only=TABLES,
)


Base = automap_base(metadata=metadata)

Base.prepare(
    generate_relationship=lambda *args, **kwargs: None,
)
