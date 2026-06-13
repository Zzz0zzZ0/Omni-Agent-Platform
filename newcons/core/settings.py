"""
全局配置中心 — 基于 Pydantic BaseSettings 的类型安全分层配置。
优先级: 环境变量 > .env 文件 > 代码默认值
"""
import os
from typing import Literal, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────────
    app_name: str = "Omni Agent Platform"
    debug: bool = False

    # ── Database (SQLite, zero external deps) ────────────────────
    database_url: str = "sqlite+aiosqlite:///./data/platform.db"

    # ── LLM Provider ────────────────────────────────────────────
    llm_provider: Literal["dashscope", "openai", "ollama"] = "dashscope"
    dashscope_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    ollama_base_url: str = "http://localhost:11434"
    default_model: str = "qwen-plus"
    default_local_model: str = "qwen3:8b"

    # ── Embedding ────────────────────────────────────────────────
    embed_model_name: str = "BAAI/bge-m3"

    # ── Security ─────────────────────────────────────────────────
    api_key_header: str = "X-API-Key"

    # ── WebSocket ────────────────────────────────────────────────
    ws_heartbeat_interval: int = 30

    # ── Proxy (optional) ─────────────────────────────────────────
    http_proxy: Optional[str] = None
    https_proxy: Optional[str] = None
    hf_endpoint: str = "https://hf-mirror.com"

    # ── CORS ─────────────────────────────────────────────────────
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    def apply_proxy(self) -> None:
        """按需设置进程级代理，仅在显式配置时生效。"""
        if self.http_proxy:
            os.environ["http_proxy"] = self.http_proxy
            os.environ["https_proxy"] = self.https_proxy or self.http_proxy
        os.environ["HF_ENDPOINT"] = self.hf_endpoint
        os.environ.setdefault("no_proxy", "localhost,127.0.0.1,0.0.0.0")


settings = Settings()
