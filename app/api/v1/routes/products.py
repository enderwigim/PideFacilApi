from fastapi import APIRouter

from app.api.v1.schemas.products.responses import ProductSchema
from app.db.session import DbSession, TenantDbContext
from app.services.products import get_product_by_id, get_products

router = APIRouter(
    prefix="/products",
    tags=["Products"],
)


# 2026-09-16 Se agrega el contexto para poder brindar los modelos o cualquier dato que podría utilizar nuestra función.
@router.get("", response_model=list[ProductSchema])
def read_products(
    db: DbSession,
    context: TenantDbContext,
):
    return get_products(
        db,
        context.models,
    )


@router.get("/{item_id}", response_model=ProductSchema)
def read_by_id(
    db: DbSession,
    context: TenantDbContext,
    item_id: str,
):
    return get_product_by_id(
        db,
        context.models,
        item_id,
    )


# @router.get("", response_model=list[ProductSchema])
# def read_products(db: DbSession, tenant: Tenant = Depends(resolve_tenant)):
#     print(tenant.id)
#     return get_products(db)


# @router.get("/{item_id}", response_model=ProductSchema)
# def read_by_id(db: DbSession, item_id: str):
#     return get_product_by_id(db, item_id)
