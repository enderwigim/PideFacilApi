from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TenantModels:
    age: Any
    epl: Any
    ite: Any
    itd: Any
    idc: Any
    bra: Any
    cus: Any
    com: Any
    cur: Any
    add: Any
    con: Any
    war: Any
    doh: Any
    dli: Any
    dof: Any
    seq: Any
    tas: Any
    ttv: Any
    uom: Any
    umc: Any
    umo: Any


# Creamos los modelos correspondientes para nuestro Tenant.
def create_tenant_models(base) -> TenantModels:
    return TenantModels(
        age=base.classes.AGENT_AGE,
        epl=base.classes.EMPLOYEE_EPL,
        ite=base.classes.ITEM_ITE,
        itd=base.classes.ITEMDATA_ITD,
        idc=base.classes.ITEMDIMCOMBINATION_IDC,
        bra=base.classes.BRANCH_BRA,
        cus=base.classes.CUSTOMER_CUS,
        com=base.classes.COMPANY_COM,
        cur=base.classes.CURRENCY_CUR,
        add=base.classes.ADDRESS_ADD,
        con=base.classes.CONTACTPERSON_CON,
        war=base.classes.WAREHOUSE_WAR,
        doh=base.classes.DOCHEADER_DOH,
        dli=base.classes.DOCLINE_DLI,
        dof=base.classes.DOCREFERENCE_DOF,
        seq=base.classes.DOCUMENTSEQUENCE_SEQ,
        tas=base.classes.TAXSYSTEM_TAS,
        ttv=base.classes.TAXTYPEVALUE_TTV,
        uom=base.classes.UNITOFMEASURE_UOM,
        umc=base.classes.UNITOFMEASURECATEGORY_UMC,
        umo=base.classes.UNITOFMEASURECONVERSION_UMO,
    )
