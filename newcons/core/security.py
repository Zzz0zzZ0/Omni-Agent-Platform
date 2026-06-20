"""
安全层 — API Key 鉴权，从请求头提取 tenant 上下文。
"""
import secrets

from fastapi import Header, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.database import get_db
from core.models.tenant import TenantModel
from core.tenant import TenantContext
from core.settings import settings


async def get_current_tenant(
    x_api_key: str = Header(..., alias=settings.api_key_header),
    db: AsyncSession = Depends(get_db),
) -> TenantContext:
    """从 API Key 解析出 TenantContext，注入到请求链路。"""
    result = await db.execute(
        select(TenantModel).where(
            TenantModel.api_key == x_api_key,
            TenantModel.is_active.is_(True),
        )
    )
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=401, detail="Invalid or inactive API key")

    return TenantContext(
        tenant_id=tenant.id,
        tenant_name=tenant.name,
        domain_id=tenant.domain_id,
        config=tenant.config or {},
    )


async def require_admin_api_key(
    x_admin_key: str | None = Header(None, alias="X-Admin-Key"),
) -> None:
    """Protect platform-admin routes when ADMIN_API_KEY is configured."""
    if not settings.admin_api_key:
        return
    if not x_admin_key or not secrets.compare_digest(x_admin_key, settings.admin_api_key):
        raise HTTPException(status_code=403, detail="Invalid admin API key")
