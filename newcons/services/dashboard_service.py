"""Dashboard business logic."""
from fastapi.concurrency import run_in_threadpool
from langchain_community.chat_models import ChatTongyi
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.logger import log
from core.models.ticket import TicketModel
from core.tenant import TenantContext
from domains.game_ops.prompts import DASHBOARD_SUMMARY_PROMPT
from domains.registry import DomainRegistry


class DashboardService:
    def __init__(self, tenant_ctx: TenantContext, db: AsyncSession):
        self.tenant_ctx = tenant_ctx
        self.db = db
        self.domain = DomainRegistry.get(tenant_ctx.domain_id)

    async def get_summary(self) -> dict:
        result = await self.db.execute(
            select(TicketModel)
            .where(TicketModel.tenant_id == self.tenant_ctx.tenant_id)
            .order_by(desc(TicketModel.created_at))
            .limit(20)
        )
        tickets = result.scalars().all()
        if not tickets:
            return {"markdown": "当前工单库为空，暂无摘要。"}

        context = "\n---\n".join(
            [
                (
                    f"Priority: {ticket.priority}\n"
                    f"Status: {ticket.status}\n"
                    f"Intent: {ticket.intent_summary}\n"
                    f"Content: {ticket.enriched_text or ticket.raw_text}"
                )
                for ticket in tickets
            ]
        )

        try:
            llm = ChatTongyi(model="qwen-plus", temperature=0.3)
            prompt = DASHBOARD_SUMMARY_PROMPT.format(context=context)
            res = await run_in_threadpool(llm.invoke, prompt)
            return {"markdown": res.content}
        except Exception as exc:
            log.warning(f"Dashboard LLM summary failed, using fallback: {exc}")
            lines = [
                f"- [{ticket.priority}] {ticket.intent_summary or ticket.raw_text[:80]}"
                for ticket in tickets[:10]
            ]
            return {"markdown": "### 最新工单摘要\n" + "\n".join(lines)}

    async def get_tickets(self) -> dict:
        result = await self.db.execute(
            select(TicketModel)
            .where(TicketModel.tenant_id == self.tenant_ctx.tenant_id)
            .order_by(desc(TicketModel.created_at))
            .limit(100)
        )
        tickets = result.scalars().all()
        return {
            "tickets": [
                {
                    "id": ticket.id,
                    "event_id": ticket.event_id,
                    "raw_text_content": ticket.raw_text,
                    "structured_content": ticket.enriched_text,
                    "sentiment_score": ticket.sentiment_score,
                    "intent_summary": ticket.intent_summary,
                    "tags": ticket.tags or [],
                    "priority": ticket.priority,
                    "is_crisis": ticket.is_crisis,
                    "action_item": ticket.action_item,
                    "recommended_operator": ticket.recommended_operator,
                    "arm_idx": ticket.arm_idx,
                    "context_vec": ticket.context_vec or [],
                    "status": ticket.status,
                    "timestamp": ticket.created_at.isoformat() if ticket.created_at else None,
                }
                for ticket in tickets
            ]
        }

    def get_domain_config(self) -> dict:
        return self.domain.get_dashboard_config()
