from pydantic import BaseModel, Field


class ServiceStatus(BaseModel):
    status: str
    message: str | None = None
    response_time_ms: float | None = None


class HealthStatus(BaseModel):
    application: str = Field(default="healthy")
    database: ServiceStatus
    redis: ServiceStatus
    version: str
    environment: str
