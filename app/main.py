from fastapi import FastAPI

from app.api.routes.customers import router as customers_router
from app.api.routes.products import router as products_router

app = FastAPI(
    title="PideFácil Integration API",
    version="1.0.0",
)


app.include_router(products_router)
app.include_router(customers_router)
