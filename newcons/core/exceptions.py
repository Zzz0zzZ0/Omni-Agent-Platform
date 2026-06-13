"""全局异常体系"""


class PlatformError(Exception):
    """平台基础异常"""
    def __init__(self, message: str = "", code: str = "PLATFORM_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)


class TenantNotFoundError(PlatformError):
    def __init__(self, tenant_id: str = ""):
        super().__init__(f"Tenant not found: {tenant_id}", "TENANT_NOT_FOUND")


class AuthenticationError(PlatformError):
    def __init__(self, detail: str = "Invalid credentials"):
        super().__init__(detail, "AUTH_ERROR")


class DomainNotFoundError(PlatformError):
    def __init__(self, domain_id: str = ""):
        super().__init__(f"Domain plugin not found: {domain_id}", "DOMAIN_NOT_FOUND")


class EngineNotReadyError(PlatformError):
    def __init__(self, detail: str = "Engine not initialized"):
        super().__init__(detail, "ENGINE_NOT_READY")


class IngestError(PlatformError):
    def __init__(self, detail: str = "Ingestion failed"):
        super().__init__(detail, "INGEST_ERROR")
