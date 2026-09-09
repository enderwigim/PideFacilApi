from fastapi import FastAPI

from app.api.routes.commercial_agent import router as commercial_agent_router
from app.api.routes.customers import router as customers_router
from app.api.routes.orders import router as order_router
from app.api.routes.products import router as products_router
from app.handlers.exception_handlers import register_exception_handlers

app = FastAPI(
    title="PideFácil Integration API",
    version="1.0.0",
)

# Exception handler
register_exception_handlers(app)

# Routers
app.include_router(products_router)
app.include_router(customers_router)
app.include_router(order_router)
app.include_router(commercial_agent_router)
