import uuid
import pytest
from httpx import ASGITransport, AsyncClient
from apps.api.app.main import app

@pytest.mark.asyncio
async def test_auth_registration_and_login_flow():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        email = f"alice_{uuid.uuid4().hex[:6]}@example.com"
        password = "SecurePassword123!"

        # 1. Register
        reg_payload = {
            "email": email,
            "password": password,
            "full_name": "Alice ML Engineer",
            "workspace_name": "Alpha ML Ops",
        }
        reg_res = await client.post("/api/v1/auth/register", json=reg_payload)
        assert reg_res.status_code == 201
        reg_data = reg_res.json()["data"]
        token = reg_data["access_token"]
        workspace_id = reg_data["workspace_id"]
        assert token is not None
        assert workspace_id is not None
        assert reg_data["role"] == "OWNER"

        # 2. Login
        login_res = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
        assert login_res.status_code == 200
        login_token = login_res.json()["data"]["access_token"]

        # 3. Get profile (/auth/me)
        headers = {"Authorization": f"Bearer {login_token}"}
        me_res = await client.get("/api/v1/auth/me", headers=headers)
        assert me_res.status_code == 200
        profile = me_res.json()["data"]
        assert profile["email"] == email
        assert len(profile["workspaces"]) >= 1
        assert profile["workspaces"][0]["role"] == "OWNER"

        # 4. Create another workspace
        ws_res = await client.post(
            "/api/v1/workspaces",
            headers=headers,
            json={"name": "Beta Workspace", "description": "Secondary research workspace"},
        )
        assert ws_res.status_code == 201
        beta_ws = ws_res.json()["data"]
        assert beta_ws["name"] == "Beta Workspace"
