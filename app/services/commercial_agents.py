from sqlalchemy.orm import Session

from app.db.models import (
    add,
    age,
    epl,
)
from app.exceptions.commercial_agent import CommercialAgentNotFound
from app.schemas.commercial_agents.responses import AgentSchema


# ----- Lecturas opcionales.
# Obtención de comerciales.
def get_commercial_agent(db: Session) -> list[AgentSchema]:
    result = []
    age_data = (
        db.query(age.age_id, age.age_name, add.add_phone1)
        .outerjoin(epl, (epl.epl_id == age.epl_age_fk))
        .outerjoin(add, (add.epl_add_fk == epl.epl_id))
        .order_by(age.age_id)
        .all()
    )
    for age_id, age_name, add_phone1 in age_data:
        result.append(
            AgentSchema(referencia=str(age_id), nombre=age_name, telefono=add_phone1)
        )
    if len(result) == 0:
        raise CommercialAgentNotFound()
    return result
