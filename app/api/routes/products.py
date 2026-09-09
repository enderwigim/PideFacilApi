from fastapi import APIRouter

from app.db.session import DbSession
from app.schemas.products.responses import ProductSchema
from app.services.products import get_product_by_id, get_products

router = APIRouter(
    prefix="/products",
    tags=["Products"],
)


@router.get("", response_model=list[ProductSchema])
def read_products(db: DbSession):
    return get_products(db)


@router.get("/{item_id}", response_model=ProductSchema)
def read_by_id(db: DbSession, item_id: str):
    return get_product_by_id(db, item_id)
