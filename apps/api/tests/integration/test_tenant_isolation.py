import io
import uuid
import pytest
from httpx import ASGITransport, AsyncClient
from apps.api.app.main import app

@pytest.mark.asyncio
async def test_cross_workspace_tenant_isolation():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Register User A in Workspace A
        uid = uuid.uuid4().hex[:6]
        reg_a = await client.post(
            "/api/v1/auth/register",
            json={
                "email": f"user_a_{uid}@tenant.com",
                "password": "Password123!",
                "full_name": "User Alpha",
                "workspace_name": f"Workspace Alpha {uid}",
            },
        )
        data_a = reg_a.json()["data"]
        token_a = data_a["access_token"]
        ws_a_id = data_a["workspace_id"]

        # Register User B in Workspace B
        reg_b = await client.post(
            "/api/v1/auth/register",
            json={
                "email": f"user_b_{uid}@tenant.com",
                "password": "Password123!",
                "full_name": "User Beta",
                "workspace_name": f"Workspace Beta {uid}",
            },
        )
        data_b = reg_b.json()["data"]
        token_b = data_b["access_token"]
        ws_b_id = data_b["workspace_id"]

        # User A uploads a dataset in Workspace A
        csv_content = b"tenure,MonthlyCharges,TotalCharges,gender,SeniorCitizen,Partner,Dependents,PhoneService,MultipleLines,InternetService,OnlineSecurity,OnlineBackup,DeviceProtection,TechSupport,StreamingTV,StreamingMovies,Contract,PaperlessBilling,PaymentMethod,Churn\n12,50.0,600.0,Female,0,Yes,No,Yes,No,DSL,Yes,No,Yes,No,No,No,Month-to-month,Yes,Electronic check,No\n"
        upload_res = await client.post(
            "/api/v1/datasets",
            headers={"Authorization": f"Bearer {token_a}", "X-Workspace-ID": ws_a_id},
            data={"name": "Confidential Tenant A Dataset"},
            files={"file": ("churn.csv", io.BytesIO(csv_content), "text/csv")},
        )
        assert upload_res.status_code == 201
        dataset_a_id = upload_res.json()["data"]["id"]

        # User B attempts to access User A's dataset using Workspace B header
        cross_res = await client.get(
            f"/api/v1/datasets/{dataset_a_id}",
            headers={"Authorization": f"Bearer {token_b}", "X-Workspace-ID": ws_b_id},
        )
        # Must be rejected (404 Not Found within Tenant B's boundary)
        assert cross_res.status_code == 404

        # User B attempts to impersonate Workspace A via header
        impersonate_res = await client.get(
            f"/api/v1/datasets/{dataset_a_id}",
            headers={"Authorization": f"Bearer {token_b}", "X-Workspace-ID": ws_a_id},
        )
        # Must be rejected (403 Forbidden - not a member of Workspace A)
        assert impersonate_res.status_code == 403
