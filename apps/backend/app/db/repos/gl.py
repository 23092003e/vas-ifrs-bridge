"""Queries for the tenant-scoped GL workflow."""

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AdjustmentEntry, GLMappingRule, GLUpload


async def tenant_mapping_rules(db: AsyncSession, tenant_id: str) -> dict[str, str]:
    rules = await db.execute(
        select(GLMappingRule.vas_code, GLMappingRule.ifrs_code)
        .where(GLMappingRule.tenant_id == tenant_id)
        .order_by(GLMappingRule.vas_code)
    )
    return dict(rules.tuples().all())


async def get_upload(
    db: AsyncSession, tenant_id: str, upload_id: str, *, lock: bool = False
) -> GLUpload:
    query = select(GLUpload).where(GLUpload.tenant_id == tenant_id, GLUpload.id == upload_id)
    result = await db.scalar(query.with_for_update() if lock else query)
    if result is None:
        raise HTTPException(404, "GL upload not found")
    return result


def journal_query(tenant_id: str, upload_id: str | None = None):
    query = select(AdjustmentEntry).where(AdjustmentEntry.tenant_id == tenant_id)
    if upload_id is not None:
        query = query.where(AdjustmentEntry.gl_upload_id == upload_id)
    return query.order_by(AdjustmentEntry.created_at, AdjustmentEntry.id)
