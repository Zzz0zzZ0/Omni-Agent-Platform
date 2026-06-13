"""
Dashboard Service — 看板数据业务逻辑。
"""
import json
from fastapi.concurrency import run_in_threadpool
from langchain_community.chat_models import ChatTongyi

from core.tenant import TenantContext
from core.logger import log
from domains.registry import DomainRegistry
from domains.game_ops.prompts import DASHBOARD_SUMMARY_PROMPT
from services.chat_service import get_vs_manager


class DashboardService:
    def __init__(self, tenant_ctx: TenantContext):
        self.tenant_ctx = tenant_ctx
        self.domain = DomainRegistry.get(tenant_ctx.domain_id)
        self.vs_manager = get_vs_manager(tenant_ctx)

    async def get_summary(self) -> dict:
        vs = self.vs_manager.get_vectorstore()
        if not vs:
            return {"markdown": "当前数据库为空，暂无摘要。"}

        docs = vs.get(limit=20, include=["documents"])
        context = "\n---\n".join(docs["documents"])

        llm = ChatTongyi(model="qwen-plus", temperature=0.3)
        prompt = DASHBOARD_SUMMARY_PROMPT.format(context=context)
        res = await run_in_threadpool(llm.invoke, prompt)
        return {"markdown": res.content}

    async def get_tickets(self) -> dict:
        vs = self.vs_manager.get_vectorstore()
        if not vs:
            return {"tickets": []}

        data = vs.get(include=["metadatas", "documents"])
        tickets = []
        for i in range(len(data["ids"])):
            meta = data["metadatas"][i]
            if "event_json" in meta:
                try:
                    ticket_data = json.loads(meta["event_json"])
                    tickets.append(ticket_data)
                except json.JSONDecodeError:
                    continue

        return {"tickets": tickets[::-1]}

    def get_domain_config(self) -> dict:
        return self.domain.get_dashboard_config()
