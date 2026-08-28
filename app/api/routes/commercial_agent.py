from fastapi import APIRouter

from app.db.session import DbSession
from app.schemas.commercial_agents.responses import AgentSchema
from app.services.read_service import get_commercial_agent

router = APIRouter(
    prefix="/optional",
    tags=["Optional reading"],
)


@router.get("/commercial_agent", response_model=list[AgentSchema])
def read_commercial_agent(db: DbSession):
    return get_commercial_agent(db)
