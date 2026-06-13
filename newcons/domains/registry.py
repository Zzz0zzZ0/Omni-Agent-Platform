"""
领域插件注册表 — 自动发现并管理所有已注册的 DomainPlugin。
"""
from typing import Dict
from domains.base import DomainPlugin
from core.logger import log


class DomainRegistry:
    _plugins: Dict[str, DomainPlugin] = {}

    @classmethod
    def register(cls, plugin: DomainPlugin) -> None:
        cls._plugins[plugin.domain_id] = plugin
        log.info(f"Domain plugin registered: {plugin.domain_id} ({plugin.display_name})")

    @classmethod
    def get(cls, domain_id: str) -> DomainPlugin:
        if domain_id not in cls._plugins:
            raise KeyError(f"Domain plugin not found: {domain_id}. Available: {list(cls._plugins.keys())}")
        return cls._plugins[domain_id]

    @classmethod
    def list_all(cls) -> list[dict]:
        return [
            {"domain_id": p.domain_id, "display_name": p.display_name}
            for p in cls._plugins.values()
        ]

    @classmethod
    def auto_discover(cls) -> None:
        """自动注册内置领域插件"""
        from domains.game_ops.plugin import GameOpsDomainPlugin
        cls.register(GameOpsDomainPlugin())
        log.info(f"Domain auto-discovery complete. {len(cls._plugins)} plugin(s) loaded.")
