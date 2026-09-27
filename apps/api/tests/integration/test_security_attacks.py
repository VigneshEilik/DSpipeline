import io
import uuid
import pytest
from httpx import ASGITransport, AsyncClient
from apps.api.app.core.config import settings
from apps.api.app.main import app

@pytest.mark.asyncio
async def test_security_malicious_csv_upload_rejection():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Register user
        uid = uuid.uuid4().hex[:6]
        reg_res = await client.post(
            "/api/v1/auth/register",
            json={
                "email": f"sec_tester_{uid}@enterprise.com",
                "password": "Password123!",
                "full_name": "Security Tester",
                "workspace_name": f"Security Workspace {uid}",
            },
        )
        assert reg_res.status_code == 201
        token = reg_res.json()["data"]["access_token"]
        workspace_id = reg_res.json()["data"]["workspace_id"]
        headers = {"Authorization": f"Bearer {token}", "X-Workspace-ID": workspace_id}

        # 1. Test binary executable header (DOS MZ header)
        fake_exe = b"MZ\x90\x00\x03\x00\x00\x00malicious_binary_content"
        res_exe = await client.post(
            "/api/v1/datasets",
            headers=headers,
            data={"name": "Fake CSV with Exe Header"},
            files={"file": ("exploit.csv", io.BytesIO(fake_exe), "text/csv")},
        )
        assert res_exe.status_code == 400
        assert "Malicious or unsupported file type detected" in res_exe.json()["error"]["message"]

        # 2. Test binary null byte injection
        null_byte_csv = b"CustomerID,Tenure,MonthlyCharges\n1,12,\x00\x00\x00binary"
        res_null = await client.post(
            "/api/v1/datasets",
            headers=headers,
            data={"name": "Null Byte CSV"},
            files={"file": ("null.csv", io.BytesIO(null_byte_csv), "text/csv")},
        )
        assert res_null.status_code == 400
        assert "contains binary data" in res_null.json()["error"]["message"]

        # 3. Test script injection in CSV header/content
        xss_csv = b"<script>alert('XSS')</script>,tenure,MonthlyCharges\n1,12,50"
        res_xss = await client.post(
            "/api/v1/datasets",
            headers=headers,
            data={"name": "XSS CSV"},
            files={"file": ("xss.csv", io.BytesIO(xss_csv), "text/csv")},
        )
        assert res_xss.status_code == 400
        assert "Malicious payload detected" in res_xss.json()["error"]["message"]

@pytest.mark.asyncio
async def test_production_bootstrap_endpoint_blocked_when_in_production(monkeypatch):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Simulate production environment
        monkeypatch.setattr(settings, "ENVIRONMENT", "production")

        res = await client.post("/api/v1/auth/bootstrap-dev")
        assert res.status_code == 403
        assert "disabled in production" in res.json()["detail"]
