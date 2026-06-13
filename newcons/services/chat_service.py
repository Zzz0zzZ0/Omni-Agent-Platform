"""
Chat Service — 从 router 中剥离的业务逻辑。
"""
import json
from fastapi.concurrency import run_in_threadpool

from core.tenant import TenantContext
from core.logger import log
from domains.base import DomainPlugin
from domains.registry import DomainRegistry
from engine.vector_store import VectorStoreManager
from engine.rag_pipeline import get_answer_complex, LocalKnowledgeTool
from agent.graph import build_graph_agent
from algorithms.linucb import LinUCBRecommender
from perception.nlp_pipeline import analyze_user_query


# ── Per-Tenant 资源缓存 ─────────────────────────────────────────
_tenant_vs_managers: dict[str, VectorStoreManager] = {}
_tenant_linucb: dict[str, LinUCBRecommender] = {}


def get_vs_manager(tenant_ctx: TenantContext) -> VectorStoreManager:
    if tenant_ctx.tenant_id not in _tenant_vs_managers:
        _tenant_vs_managers[tenant_ctx.tenant_id] = VectorStoreManager(tenant_ctx)
    return _tenant_vs_managers[tenant_ctx.tenant_id]


def get_linucb(tenant_ctx: TenantContext, domain: DomainPlugin) -> LinUCBRecommender:
    if tenant_ctx.tenant_id not in _tenant_linucb:
        _tenant_linucb[tenant_ctx.tenant_id] = LinUCBRecommender(
            operators=domain.get_ticket_operators(),
            tag_keywords=domain.get_tag_keywords(),
        )
    return _tenant_linucb[tenant_ctx.tenant_id]


def _clean_llm_output(raw_output) -> str:
    if isinstance(raw_output, str) and raw_output.strip().startswith("[{"):
        try:
            raw_output = json.loads(raw_output.strip())
        except json.JSONDecodeError:
            pass
    if isinstance(raw_output, list):
        texts = [
            item.get("text", "")
            for item in raw_output
            if isinstance(item, dict) and "text" in item
        ]
        if texts:
            return "".join(texts)
    return str(raw_output)


class ChatService:
    def __init__(self, tenant_ctx: TenantContext):
        self.tenant_ctx = tenant_ctx
        self.domain = DomainRegistry.get(tenant_ctx.domain_id)
        self.vs_manager = get_vs_manager(tenant_ctx)
        self.linucb = get_linucb(tenant_ctx, self.domain)

    async def chat(
        self,
        query: str,
        use_agent: bool = True,
        model_type: str = "cloud",
        use_auto_alpha: bool = True,
        alpha: float = 0.5,
        use_emotion: bool = True,
        k_param: int = 3,
        temp_param: float = 0.1,
    ) -> dict:
        vs = self.vs_manager.get_vectorstore()
        bm25 = self.vs_manager.get_bm25()
        embeddings = self.vs_manager.embeddings

        if use_agent:
            # 构建 agent tools (包含本地知识库)
            local_tool = None
            if vs and bm25:
                lkt = LocalKnowledgeTool(vs, bm25, embeddings, self.linucb)
                local_tool = lkt.get_tool()

            tools = self.domain.get_tools(local_knowledge_tool=local_tool)
            system_prompt = self.domain.get_agent_system_prompt()

            agent_app = build_graph_agent(
                tools, system_prompt,
                model_type=model_type,
                temp_param=temp_param,
            )
            response = await run_in_threadpool(
                agent_app.invoke, {"messages": [("user", query)]}
            )

            raw_content = response["messages"][-1].content
            answer = _clean_llm_output(raw_content)

            thoughts = []
            for msg in response["messages"][1:-1]:
                if msg.type == "ai" and getattr(msg, "tool_calls", None):
                    for tc in msg.tool_calls:
                        thoughts.append(f"Tool Call: {tc['name']}")

            # 旁路感知
            persona_tags = []
            arm_idx = -1
            context_vec = []
            if use_emotion:
                try:
                    perception_schema = self.domain.get_perception_schema()
                    emotion, _, persona_tags = await run_in_threadpool(
                        analyze_user_query, query,
                        perception_schema=perception_schema,
                        model_type=model_type, temp_val=temp_param,
                    )
                except Exception as e:
                    log.warning(f"旁路画像提取失败: {e}")

            return {
                "answer": answer,
                "thoughts": thoughts,
                "persona": persona_tags,
                "arm_idx": arm_idx,
                "context_vec": context_vec,
            }

        else:
            perception_fn = None
            perception_schema = self.domain.get_perception_schema()
            if use_emotion:
                def perception_fn(q, model_type="cloud", temp_val=0.1):
                    return analyze_user_query(q, perception_schema, model_type=model_type, temp_val=temp_val)

            result = await run_in_threadpool(
                get_answer_complex,
                vs, bm25, query,
                embeddings=embeddings,
                linucb=self.linucb,
                perception_fn=perception_fn,
                model_type=model_type,
                alpha=alpha,
                use_auto_alpha=use_auto_alpha,
                use_emotion=use_emotion,
                k_param=k_param,
                temp_param=temp_param,
            )

            return {
                "answer": _clean_llm_output(result["answer"]),
                "thoughts": [],
                "persona": result.get("persona", []),
                "arm_idx": result.get("arm_idx", -1),
                "context_vec": result.get("context_vec", []),
                "emotion": result.get("emotion", "neutral"),
            }
