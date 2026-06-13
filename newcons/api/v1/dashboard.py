"""GET /api/v1/dashboard/*"""
from fastapi import APIRouter, Depends, HTTPException

from api.deps import get_dashboard_service
from services.dashboard_service import DashboardService

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])


@router.get("/summary")
async def dashboard_summary(
    svc: DashboardService = Depends(get_dashboard_service),
):
    try:
        return await svc.get_summary()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tickets")
async def get_dashboard_tickets(
    svc: DashboardService = Depends(get_dashboard_service),
):
    try:
        return await svc.get_tickets()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config")
async def get_dashboard_config(
    svc: DashboardService = Depends(get_dashboard_service),
):
    """返回当前 domain 的看板配置（角色列表等）"""
    return svc.get_domain_config()
