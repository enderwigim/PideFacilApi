from collections.abc import Generator  # noqa: N999
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.database_20260921 import SessionLocal


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


DbSession = Annotated[Session, Depends(get_db)]
