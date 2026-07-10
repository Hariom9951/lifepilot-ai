import pytest
from httpx import AsyncClient

# Mark all test cases in this module as asynchronous
pytestmark = pytest.mark.asyncio


async def test_root_endpoint(client: AsyncClient) -> None:
    """
    Test the root health check path.
    """
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["project"] == "LifePilot AI"
    assert data["status"] == "running"
    assert "version" in data


async def test_api_v1_health_endpoint(client: AsyncClient) -> None:
    """
    Test the /api/v1/health status checks endpoint.
    """
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["success"] is True

    health = res_json["data"]
    assert health["application"] in ("healthy", "degraded")
    assert health["database"]["status"] == "healthy"
    assert "version" in health
    assert "environment" in health
