from fastapi import APIRouter

from app.db.session import DbSession
from app.schemas.product import ProductSchema
from app.services.read_service import get_products

router = APIRouter(
    prefix="/products",
    tags=["Products"],
)


@router.get("", response_model=list[ProductSchema])
def read_products(db: DbSession):
    return get_products(db)
