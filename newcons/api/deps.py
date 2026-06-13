"""
FastAPI 依赖注入汇总。
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.security import get_current_tenant
from core.tenant import TenantContext
from services.chat_service import ChatService
from services.ingest_service import IngestService
from services.dashboard_service import DashboardService
from services.ticket_service import TicketService


async def get_chat_service(
    tenant: TenantContext = Depends(get_current_tenant),
) -> ChatService:
    return ChatService(tenant)


async def get_ingest_service(
    tenant: TenantContext = Depends(get_current_tenant),
) -> IngestService:
    return IngestService(tenant)


async def get_dashboard_service(
    tenant: TenantContext = Depends(get_current_tenant),
) -> DashboardService:
    return DashboardService(tenant)


async def get_ticket_service(
    tenant: TenantContext = Depends(get_current_tenant),
) -> TicketService:
    return TicketService(tenant)
