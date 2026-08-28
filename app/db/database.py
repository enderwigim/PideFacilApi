from sqlalchemy import MetaData, create_engine
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    echo=settings.debug,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)

metadata = MetaData()


TABLES = [
    "ITEM_ITE",
    "ITEMDATA_ITD",
    "ITEMDIMCOMBINATION_IDC",
    "DOCLINE_DLI",
    "DOCHEADER_DOH",
    "DOCREFERENCE_DOF",
    "DOCUMENTSEQUENCE_SEQ",
    "TAXSYSTEM_TAS",
    "TAXTYPEVALUE_TTV",
    "CUSTOMER_CUS",
    "COMPANY_COM",
    "CURRENCY_CUR",
    "AGENT_AGE",
    "EMPLOYEE_EPL",
    "ADDRESS_ADD",
    "CONTACTPERSON_CON",
    "UNITOFMEASURE_UOM",
    "UNITOFMEASURECATEGORY_UMC",
    "UNITOFMEASURECONVERSION_UMO",
    "EMPLOYEE_EPL",
]


metadata.reflect(
    bind=engine,
    only=TABLES,
)


Base = automap_base(metadata=metadata)

Base.prepare(
    generate_relationship=lambda *args, **kwargs: None,
)
