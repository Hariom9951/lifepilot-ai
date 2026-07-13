from pydantic import BaseModel, Field


class ServiceStatus(BaseModel):
    # Possible values: "healthy" | "unhealthy" | "disabled"
    # "disabled" means the service is intentionally not configured.
    status: str
    message: str | None = None
    response_time_ms: float | None = None


class HealthStatus(BaseModel):
    application: str = Field(default="healthy")
    database: ServiceStatus
    redis: ServiceStatus
    version: str
    environment: str
