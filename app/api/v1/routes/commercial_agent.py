from fastapi import APIRouter

from app.api.v1.schemas.commercial_agents.responses import AgentSchema
from app.db.session import DbSession, TenantDbContext
from app.services.commercial_agents import get_commercial_agent

router = APIRouter(
    prefix="/optional",
    tags=["Optional reading"],
)


@router.get("/commercial_agent", response_model=list[AgentSchema])
def read_commercial_agent(db: DbSession, context: TenantDbContext):
    return get_commercial_agent(db, models=context.models)
