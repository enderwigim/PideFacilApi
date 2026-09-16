from fastapi import APIRouter, Depends

from app.api.v1.schemas.products.responses import ProductSchema
from app.core.tenancy.resolver import resolve_tenant
from app.core.tenancy.tenant import Tenant
from app.db.session import DbSession
from app.services.products import get_product_by_id, get_products

router = APIRouter(
    prefix="/products",
    tags=["Products"],
)


@router.get("", response_model=list[ProductSchema])
def read_products(db: DbSession, tenant: Tenant = Depends(resolve_tenant)):
    print(tenant.id)
    return get_products(db)


@router.get("/{item_id}", response_model=ProductSchema)
def read_by_id(db: DbSession, item_id: str):
    return get_product_by_id(db, item_id)
