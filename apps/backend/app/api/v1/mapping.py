"""Tenant mapping rules. Each rule overrides one source account code."""

from typing import Annotated

from fastapi import APIRouter, Path
from pydantic import BaseModel
from sqlalchemy.dialects.postgresql import insert

from app.db.models import GLMappingRule
from app.db.repos.gl import tenant_mapping_rules
from app.deps import DB, Workspace
from app.gl.adjustments import AccountCode

router = APIRouter()


class MappingUpdate(BaseModel):
    ifrs_code: AccountCode


@router.get("/")
async def list_mappings(db: DB, tenant: Workspace) -> list[dict]:
    rules = await tenant_mapping_rules(db, tenant.id)
    return [{"vas_code": code, "ifrs_code": target} for code, target in rules.items()]


@router.put("/{rule_id}")
async def update_mapping(
    rule_id: Annotated[str, Path(min_length=1, max_length=50, pattern=r"^\S+$")],
    body: MappingUpdate,
    db: DB,
    tenant: Workspace,
) -> dict:
    statement = insert(GLMappingRule).values(
        tenant_id=tenant.id, vas_code=rule_id, ifrs_code=body.ifrs_code
    )
    await db.execute(
        statement.on_conflict_do_update(
            index_elements=["tenant_id", "vas_code"],
            set_={"ifrs_code": statement.excluded.ifrs_code},
        )
    )
    await db.commit()
    return {"vas_code": rule_id, "ifrs_code": body.ifrs_code}
