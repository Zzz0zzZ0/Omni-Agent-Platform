"""
租户管理 CRUD — 供平台管理员使用 (不需要 tenant 鉴权)。
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.database import get_db
from core.models.tenant import TenantModel
from core.security import require_admin_api_key
from api.schemas import TenantCreate, TenantResponse
from domains.registry import DomainRegistry

router = APIRouter(
    prefix="/api/v1/tenants",
    tags=["tenants"],
    dependencies=[Depends(require_admin_api_key)],
)


@router.post("/", response_model=TenantResponse)
async def create_tenant(
    req: TenantCreate,
    db: AsyncSession = Depends(get_db),
):
    # 验证 domain 存在
    try:
        DomainRegistry.get(req.domain_id)
    except KeyError:
        raise HTTPException(400, f"Unknown domain: {req.domain_id}")

    tenant = TenantModel(name=req.name, domain_id=req.domain_id, config=req.config)
    db.add(tenant)
    await db.flush()
    await db.refresh(tenant)

    return TenantResponse(
        id=tenant.id,
        name=tenant.name,
        api_key=tenant.api_key,
        domain_id=tenant.domain_id,
        is_active=tenant.is_active,
    )


@router.get("/", response_model=list[TenantResponse])
async def list_tenants(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TenantModel).where(TenantModel.is_active.is_(True)))
    tenants = result.scalars().all()
    return [
        TenantResponse(
            id=t.id, name=t.name, api_key=t.api_key,
            domain_id=t.domain_id, is_active=t.is_active,
        )
        for t in tenants
    ]


@router.get("/domains/available")
async def list_domains():
    return DomainRegistry.list_all()


@router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(tenant_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TenantModel).where(TenantModel.id == tenant_id))
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(404, "Tenant not found")
    return TenantResponse(
        id=tenant.id, name=tenant.name, api_key=tenant.api_key,
        domain_id=tenant.domain_id, is_active=tenant.is_active,
    )
