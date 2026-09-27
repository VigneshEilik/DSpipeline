import asyncio
import io
import uuid
import pytest
from httpx import ASGITransport, AsyncClient
from apps.api.app.main import app
from apps.api.app.modules.deployments.serving_cache import serving_cache
from ml.pipelines.ingestion.generator import generate_telco_churn_dataset

@pytest.mark.asyncio
async def test_multi_version_serving_and_rollback_consistency():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Register User and Workspace
        uid = uuid.uuid4().hex[:6]
        reg_res = await client.post(
            "/api/v1/auth/register",
            json={
                "email": f"serving_eng_{uid}@enterprise.com",
                "password": "Password123!",
                "full_name": "Serving Reliability Engineer",
                "workspace_name": f"Serving Consistency Ops {uid}",
            },
        )
        assert reg_res.status_code == 201
        auth_data = reg_res.json()["data"]
        token = auth_data["access_token"]
        workspace_id = auth_data["workspace_id"]
        headers = {"Authorization": f"Bearer {token}", "X-Workspace-ID": workspace_id}

        # 2. Upload Dataset
        df = generate_telco_churn_dataset(n_samples=250, random_state=42)
        csv_bytes = df.to_csv(index=False).encode("utf-8")
        upload_res = await client.post(
            "/api/v1/datasets",
            headers=headers,
            data={"name": f"Serving Test Dataset {uid}"},
            files={"file": ("dataset.csv", io.BytesIO(csv_bytes), "text/csv")},
        )
        assert upload_res.status_code == 201
        dataset_version_id = upload_res.json()["data"]["versions"][0]["id"]

        # 3. Train Model 1 (Logistic Regression)
        exp1_res = await client.post(
            "/api/v1/experiments",
            headers=headers,
            json={
                "name": "Model Version 1 - LR",
                "dataset_version_id": dataset_version_id,
                "algorithm": "logistic_regression",
            },
        )
        exp1_id = exp1_res.json()["data"]["id"]
        for _ in range(20):
            await asyncio.sleep(0.4)
            poll = await client.get(f"/api/v1/experiments/{exp1_id}", headers=headers)
            if poll.json()["data"]["status"] == "COMPLETED":
                break

        # Register & Approve Model 1
        m1_reg = await client.post(
            "/api/v1/models",
            headers=headers,
            json={"name": "Production Churn Pipeline", "experiment_id": exp1_id},
        )
        model_id = m1_reg.json()["data"]["id"]
        v1_id = m1_reg.json()["data"]["versions"][0]["id"]
        await client.post(
            f"/api/v1/models/{model_id}/approve",
            headers=headers,
            json={"version_id": v1_id, "decision": "APPROVED", "comments": "Model v1 approved"},
        )

        # 4. Train Model 2 (Random Forest)
        exp2_res = await client.post(
            "/api/v1/experiments",
            headers=headers,
            json={
                "name": "Model Version 2 - RF",
                "dataset_version_id": dataset_version_id,
                "algorithm": "random_forest",
            },
        )
        exp2_id = exp2_res.json()["data"]["id"]
        for _ in range(20):
            await asyncio.sleep(0.4)
            poll = await client.get(f"/api/v1/experiments/{exp2_id}", headers=headers)
            if poll.json()["data"]["status"] == "COMPLETED":
                break

        # Register & Approve Model 2
        m2_reg = await client.post(
            "/api/v1/models",
            headers=headers,
            json={"name": "Production Churn Pipeline", "experiment_id": exp2_id},
        )
        v2_id = m2_reg.json()["data"]["latest_version"]["id"]
        await client.post(
            f"/api/v1/models/{model_id}/approve",
            headers=headers,
            json={"version_id": v2_id, "decision": "APPROVED", "comments": "Model v2 approved"},
        )

        # 5. Deploy Model v1
        deploy_res = await client.post(
            "/api/v1/deployments",
            headers=headers,
            json={"name": "Churn Realtime Service", "model_version_id": v1_id},
        )
        assert deploy_res.status_code == 201
        deployment_id = deploy_res.json()["data"]["id"]

        test_features = {
            "gender": "Female",
            "tenure": 12,
            "MonthlyCharges": 75.0,
            "TotalCharges": 900.0,
            "Contract": "Month-to-month",
            "InternetService": "Fiber optic",
            "OnlineSecurity": "No",
            "TechSupport": "No",
            "PaymentMethod": "Electronic check",
            "PaperlessBilling": "Yes",
            "SeniorCitizen": 0,
            "Partner": "No",
            "Dependents": "No",
            "PhoneService": "Yes",
            "MultipleLines": "No",
            "OnlineBackup": "No",
            "DeviceProtection": "No",
            "StreamingTV": "No",
            "StreamingMovies": "No",
        }

        # Predict with v1
        pred1 = await client.post("/api/v1/predictions", headers=headers, json={"features": test_features})
        assert pred1.status_code == 201, f"Pred1 failed: {pred1.status_code} - {pred1.text}"
        assert pred1.json()["data"]["model_version_id"] == v1_id

        # 6. Promote Model v2 (Roll forward)
        deploy2_res = await client.post(
            "/api/v1/deployments",
            headers=headers,
            json={"name": "Churn Realtime Service V2", "model_version_id": v2_id},
        )
        assert deploy2_res.status_code == 201, f"Deploy2 failed: {deploy2_res.status_code} - {deploy2_res.text}"
        deployment2_id = deploy2_res.json()["data"]["id"]

        # Predict with v2
        pred2 = await client.post("/api/v1/predictions", headers=headers, json={"features": test_features})
        assert pred2.status_code == 201
        assert pred2.json()["data"]["model_version_id"] == v2_id

        # 7. Atomic Rollback to v1
        rollback_res = await client.post(
            f"/api/v1/deployments/{deployment2_id}/rollback",
            headers=headers,
            json={"target_model_version_id": v1_id, "reason": "Slight latency degradation on v2"},
        )
        assert rollback_res.status_code == 200

        # Predict again - must immediately observe v1 across any process reading DB state
        pred3 = await client.post("/api/v1/predictions", headers=headers, json={"features": test_features})
        assert pred3.status_code == 201
        assert pred3.json()["data"]["model_version_id"] == v1_id
        assert pred3.json()["data"]["risk_category"].upper() in ["LOW", "MEDIUM", "HIGH"]
