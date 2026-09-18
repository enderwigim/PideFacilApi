from fastapi import APIRouter

from app.api.v1.routes.commercial_agent import router as commercial_agent_router
from app.api.v1.routes.customers import router as customers_router
from app.api.v1.routes.orders import router as order_router
from app.api.v1.routes.products import router as products_router

router = APIRouter()

# Routers
router.include_router(products_router)
router.include_router(customers_router)
router.include_router(order_router)
router.include_router(commercial_agent_router)
