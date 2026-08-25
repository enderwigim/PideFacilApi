from fastapi import FastAPI

from app.api.routes.products import router as products_router

app = FastAPI(
    title="PideFácil Integration API",
    version="1.0.0",
)


app.include_router(products_router)
