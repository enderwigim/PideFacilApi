from fastapi import FastAPI
from sqlalchemy import text

from app.db.session import DbSession

app = FastAPI(
    title="PideFácil Integration API",
    version="1.0.0",
)


@app.get("/health")
async def health(db: DbSession):
    await db.execute(text("SELECT 1"))

    return {
        "status": "ok",
        "database": "connected",
    }
