"""
Ingest Service — 文档/反馈摄入业务逻辑。
"""
import os
import tempfile
from typing import List

from fastapi import UploadFile
from fastapi.concurrency import run_in_threadpool
from langchain_core.documents import Document
from sqlalchemy.ext.asyncio import AsyncSession

from core.tenant import TenantContext
from core.models.ticket import TicketModel
from core.logger import log
from domains.registry import DomainRegistry
from domains.game_ops.schemas import FeedbackEvent
from engine.ingestion import IngestionPipeline
from engine.vector_store import VectorStoreManager
from agent.pipelines.ticket import build_ticket_pipeline
from algorithms.linucb import LinUCBRecommender
from services.chat_service import get_vs_manager, get_linucb
from services.websocket_manager import ws_manager


_ingestion_pipeline = IngestionPipeline()
_ticket_pipeline = build_ticket_pipeline()


class IngestService:
    def __init__(self, tenant_ctx: TenantContext, db: AsyncSession | None = None):
        self.tenant_ctx = tenant_ctx
        self.db = db
        self.domain = DomainRegistry.get(tenant_ctx.domain_id)
        self.vs_manager = get_vs_manager(tenant_ctx)
        self.linucb = get_linucb(tenant_ctx, self.domain)

    async def ingest_document(self, file: UploadFile) -> dict:
        """上传知识库文档"""
        allowed = {".pdf", ".txt"}
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in allowed:
            raise ValueError(f"Unsupported file type. Supported: {', '.join(allowed)}")

        file_content = await file.read()
        if len(file_content) > 50 * 1024 * 1024:
            raise ValueError("文件过大，最大允许 50MB")
        if not file_content or not file_content.strip():
            raise ValueError("文件内容为空")

        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
            tmp.write(file_content)
            tmp_path = tmp.name

        try:
            vs, splits, count = await run_in_threadpool(
                self.vs_manager.ingest_file, tmp_path
            )
            viz_df = self.vs_manager.visualize_semantic_space()
            viz_data = viz_df.to_dict(orient="records") if viz_df is not None else []

            return {
                "status": "success",
                "message": f"Memory solidified, {count} fragments processed.",
                "viz_data": viz_data,
            }
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    async def ingest_feedback(
        self,
        feedback_text: str | None = None,
        doc_file: UploadFile | None = None,
        images: List[UploadFile] = [],
    ) -> dict:
        """摄入玩家反馈 (文本 + 图片 + OCR)，触发工单流水线"""
        tmp_files = []
        try:
            doc_path = None
            if doc_file:
                with tempfile.NamedTemporaryFile(
                    delete=False, suffix=os.path.splitext(doc_file.filename)[1]
                ) as tmp:
                    tmp.write(await doc_file.read())
                    doc_path = tmp.name
                    tmp_files.append(doc_path)

            img_paths = []
            for img_file in images:
                with tempfile.NamedTemporaryFile(
                    delete=False, suffix=os.path.splitext(img_file.filename)[1]
                ) as tmp:
                    tmp.write(await img_file.read())
                    img_paths.append(tmp.name)
                    tmp_files.append(tmp.name)

            event = await run_in_threadpool(
                _ingestion_pipeline.run,
                text_content=feedback_text,
                text_file_path=doc_path,
                image_paths=img_paths,
            )

            # Persist to vector memory when a tenant knowledge base already exists.
            vs = self.vs_manager.get_vectorstore()
            if vs:
                doc = Document(
                    page_content=event.get_enriched_text(),
                    metadata={
                        "event_id": event.event_id,
                        "timestamp": event.timestamp,
                        "event_json": event.model_dump_json(),
                    },
                )
                self.vs_manager.add_document(doc)

            pipeline_result = await self._run_ticket_pipeline(event, vs)
            ticket = await self._persist_ticket(event, pipeline_result)

            return {
                "status": "success",
                "event_id": event.event_id,
                "ticket_id": ticket.id if ticket else None,
                "ocr_summary": [r.model_dump() for r in event.ocr_results],
                "enriched_text_preview": event.get_enriched_text()[:200],
            }
        finally:
            for f in tmp_files:
                if os.path.exists(f):
                    os.remove(f)

    async def _run_ticket_pipeline(self, event: FeedbackEvent, vs) -> dict:
        """运行工单流水线并通过 WebSocket 推送结果"""
        try:
            inputs = {
                "event": event,
                "domain": self.domain,
                "linucb": self.linucb,
                "vectorstore": vs,
                "alert_triggered": False,
            }
            result = await run_in_threadpool(_ticket_pipeline.invoke, inputs)

            # WebSocket 广播
            await ws_manager.broadcast(
                self.tenant_ctx.tenant_id,
                "ticket_processed",
                {
                    "event_id": event.event_id,
                    "recommended_operator": result.get("recommended_operator", ""),
                    "priority": result.get("routing", {}).priority if hasattr(result.get("routing", {}), "priority") else "P3",
                    "alert_triggered": result.get("alert_triggered", False),
                },
            )
            return result
        except Exception as e:
            log.error(f"[Pipeline Error] Ticket pipeline failed: {e}")
            return {
                "sentiment": None,
                "routing": None,
                "recommended_operator": "",
                "arm_idx": -1,
                "context_vec": [],
                "alert_triggered": False,
            }

    async def _persist_ticket(self, event: FeedbackEvent, pipeline_result: dict) -> TicketModel | None:
        """Persist the processed feedback as the system-of-record ticket."""
        if self.db is None:
            return None

        sentiment = pipeline_result.get("sentiment")
        routing = pipeline_result.get("routing")
        ticket = TicketModel(
            tenant_id=self.tenant_ctx.tenant_id,
            event_id=event.event_id,
            raw_text=event.raw_text_content,
            enriched_text=event.get_enriched_text(),
            sentiment_score=getattr(sentiment, "sentiment_score", 0),
            intent_summary=getattr(sentiment, "intent_summary", ""),
            tags=getattr(routing, "tags", []) or [],
            priority=getattr(routing, "priority", "P3") or "P3",
            is_crisis=bool(getattr(routing, "is_crisis", False)),
            action_item=getattr(routing, "action_item", "") or "",
            recommended_operator=pipeline_result.get("recommended_operator", "") or "",
            arm_idx=pipeline_result.get("arm_idx", -1),
            context_vec=pipeline_result.get("context_vec", []) or [],
            status="open",
        )
        self.db.add(ticket)
        await self.db.flush()
        await self.db.refresh(ticket)
        return ticket
