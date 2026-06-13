"""
应用入口 — 替代旧 api/server.py。
"""
import os
import sys

# 确保 newcons 在 path 中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.settings import settings
from core.database import init_db
from core.logger import log
from domains.registry import DomainRegistry
from api.v1 import (
    chat_router,
    ingest_router,
    dashboard_router,
    feedback_router,
    tenants_router,
    ws_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ──
    settings.apply_proxy()
    await init_db()
    DomainRegistry.auto_discover()
    log.info(f"{settings.app_name} started successfully")
    yield
    # ── Shutdown ──
    log.info(f"{settings.app_name} shutting down")


app = FastAPI(
    title=settings.app_name,
    description="B2B Game Ops AI Platform — Multi-tenant, Domain-pluggable",
    version="3.0.0",
    lifespan=lifespan,
)

# ── CORS ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ──
app.include_router(chat_router)
app.include_router(ingest_router)
app.include_router(dashboard_router)
app.include_router(feedback_router)
app.include_router(tenants_router)
app.include_router(ws_router)


@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "3.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
