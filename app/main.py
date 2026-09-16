from fastapi import FastAPI

from app.api.v1.router import router as v1_router
from app.handlers.exception_handlers import register_exception_handlers

# En el titulo colocaremos la última versión publicada
app = FastAPI(
    title="PideFácil Integration API",
    version="1.0.0",
)

# Exception handler
register_exception_handlers(app)

# Routers
app.include_router(
    v1_router,
    prefix="/v1",
)
