import pytest
from httpx import ASGITransport, AsyncClient
from apps.api.app.main import app

@pytest.mark.asyncio
async def test_liveness_check():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/healthz")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "timestamp" in data

@pytest.mark.asyncio
async def test_readiness_check():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/readyz")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert data["database"] == "connected"

@pytest.mark.asyncio
async def test_metrics_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/metrics")
        assert response.status_code == 200
        assert "modelops_http_requests_total" in response.text
