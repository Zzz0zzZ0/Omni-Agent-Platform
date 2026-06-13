"""
Ticket Service — 工单与反馈奖励管理。
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.tenant import TenantContext
from core.models.feedback import FeedbackLogModel
from core.models.ticket import TicketModel
from core.logger import log
from domains.registry import DomainRegistry
from services.chat_service import get_linucb


class TicketService:
    def __init__(self, tenant_ctx: TenantContext):
        self.tenant_ctx = tenant_ctx
        self.domain = DomainRegistry.get(tenant_ctx.domain_id)
        self.linucb = get_linucb(tenant_ctx, self.domain)

    async def update_recommendation_reward(self, arm_idx: int, context_vec: list, reward: float) -> dict:
        """更新 LinUCB 推荐奖励"""
        self.linucb.update_reward(arm_idx, context_vec, reward)
        return {"status": "success", "message": f"Operator feedback recorded for arm {arm_idx}."}

    async def log_negative_feedback(self, db: AsyncSession, query: str, emotion: str, persona: str) -> None:
        """记录负面反馈到数据库"""
        feedback = FeedbackLogModel(
            tenant_id=self.tenant_ctx.tenant_id,
            player_query=query,
            emotion=emotion,
            player_persona=persona,
        )
        db.add(feedback)
        log.info(f"[Tenant:{self.tenant_ctx.tenant_id}] Logged negative feedback")
