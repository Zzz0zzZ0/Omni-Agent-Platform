"""
多租户上下文 — 每请求注入，下游通过此对象获取隔离资源。
"""
from dataclasses import dataclass, field


@dataclass
class TenantContext:
    tenant_id: str
    tenant_name: str
    domain_id: str = "game_ops"
    config: dict = field(default_factory=dict)

    @property
    def chroma_collection_name(self) -> str:
        return f"tenant_{self.tenant_id}_vectors"

    @property
    def data_dir(self) -> str:
        return f"./data/tenants/{self.tenant_id}"

    @property
    def chroma_persist_dir(self) -> str:
        return f"{self.data_dir}/chroma"
