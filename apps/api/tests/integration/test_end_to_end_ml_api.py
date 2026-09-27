import asyncio
import io
import uuid
import pytest
from httpx import ASGITransport, AsyncClient
from apps.api.app.main import app
from ml.pipelines.ingestion.generator import generate_telco_churn_dataset

@pytest.mark.asyncio
async def test_complete_mlops_lifecycle_api():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Register User & Obtain Workspace
        uid = uuid.uuid4().hex[:6]
        reg_res = await client.post(
            "/api/v1/auth/register",
            json={
                "email": f"lead_ml_{uid}@enterprise.com",
                "password": "Password123!",
                "full_name": "Lead ML Engineer",
                "workspace_name": f"Churn Prediction Ops {uid}",
            },
        )
        assert reg_res.status_code == 201
        auth_data = reg_res.json()["data"]
        token = auth_data["access_token"]
        workspace_id = auth_data["workspace_id"]
        headers = {"Authorization": f"Bearer {token}", "X-Workspace-ID": workspace_id}

        # 2. Upload Sample Churn Dataset
        df = generate_telco_churn_dataset(n_samples=300, random_state=42)
        csv_bytes = df.to_csv(index=False).encode("utf-8")

        upload_res = await client.post(
            "/api/v1/datasets",
            headers=headers,
            data={"name": "Telco Churn Training 300", "description": "Benchmark evaluation dataset"},
            files={"file": ("telco_churn.csv", io.BytesIO(csv_bytes), "text/csv")},
        )
        assert upload_res.status_code == 201
        dataset_data = upload_res.json()["data"]
        dataset_id = dataset_data["id"]
        dataset_version_id = dataset_data["versions"][0]["id"]
        assert dataset_data["latest_validation"]["is_valid"] is True

        # 3. Preview Dataset Rows
        preview_res = await client.get(
            f"/api/v1/datasets/{dataset_id}/preview?page=1&page_size=5",
            headers=headers,
        )
        assert preview_res.status_code == 200
        preview = preview_res.json()["data"]
        assert len(preview["rows"]) == 5
        assert "MonthlyCharges" in preview["columns"]

        # 4. Trigger Training Experiment
        exp_res = await client.post(
            "/api/v1/experiments",
            headers=headers,
            json={
                "name": "Logistic Regression Churn Baseline",
                "dataset_version_id": dataset_version_id,
                "algorithm": "logistic_regression",
                "random_seed": 42,
            },
        )
        assert exp_res.status_code == 201
        exp_data = exp_res.json()["data"]
        experiment_id = exp_data["id"]

        # 5. Poll for Training Completion (Async Task execution)
        for _ in range(20):
            await asyncio.sleep(0.5)
            poll_res = await client.get(f"/api/v1/experiments/{experiment_id}", headers=headers)
            poll_data = poll_res.json()["data"]
            if poll_data["status"] in ["COMPLETED", "FAILED"]:
                break

        assert poll_data["status"] == "COMPLETED"
        assert poll_data["metrics"] is not None
        assert poll_data["metrics"]["accuracy"] > 0.50
        assert poll_data["metrics"]["f1_score"] > 0.40

        # 6. Register Model in Model Registry
        reg_model_res = await client.post(
            "/api/v1/models",
            headers=headers,
            json={
                "name": "Customer Churn Predictor",
                "experiment_id": experiment_id,
                "description": "Production candidate model",
            },
        )
        assert reg_model_res.status_code == 201
        model_data = reg_model_res.json()["data"]
        model_id = model_data["id"]
        version_id = model_data["versions"][0]["id"]
        assert model_data["versions"][0]["lifecycle_stage"] == "EVALUATED"

        # 7. Approve Model Version
        approve_res = await client.post(
            f"/api/v1/models/{model_id}/approve",
            headers=headers,
            json={
                "version_id": version_id,
                "decision": "APPROVED",
                "comments": "Meets F1 and ROC-AUC criteria for production.",
            },
        )
        assert approve_res.status_code == 200
        assert approve_res.json()["data"]["lifecycle_stage"] == "APPROVED"

        # 8. Deploy Approved Model
        deploy_res = await client.post(
            "/api/v1/deployments",
            headers=headers,
            json={
                "name": "Churn Realtime API Prod",
                "model_version_id": version_id,
                "environment": "production",
                "traffic_percentage": 100,
            },
        )
        assert deploy_res.status_code == 201, f"Deploy failed: {deploy_res.status_code} - {deploy_res.text}"
        deployment_data = deploy_res.json()["data"]
        deployment_id = deployment_data["id"]
        assert deployment_data["status"] == "ACTIVE"

        # 9. Real-Time Single Prediction
        test_customer = {
            "tenure": 2,
            "MonthlyCharges": 85.5,
            "TotalCharges": 171.0,
            "gender": "Female",
            "SeniorCitizen": 0,
            "Partner": "No",
            "Dependents": "No",
            "PhoneService": "Yes",
            "MultipleLines": "No",
            "InternetService": "Fiber optic",
            "OnlineSecurity": "No",
            "OnlineBackup": "No",
            "DeviceProtection": "No",
            "TechSupport": "No",
            "StreamingTV": "Yes",
            "StreamingMovies": "Yes",
            "Contract": "Month-to-month",
            "PaperlessBilling": "Yes",
            "PaymentMethod": "Electronic check",
        }

        pred_res = await client.post(
            "/api/v1/predictions",
            headers=headers,
            json={"deployment_id": deployment_id, "features": test_customer},
        )
        assert pred_res.status_code == 201
        pred_data = pred_res.json()["data"]
        assert pred_data["prediction_label"] in ["Yes", "No"]
        assert 0.0 <= pred_data["prediction_probability"] <= 1.0
        assert pred_data["risk_category"] in ["Low", "Medium", "High"]
        assert pred_data["latency_ms"] > 0

        # 10. Verify Prediction History Persistence
        history_res = await client.get("/api/v1/predictions", headers=headers)
        assert history_res.status_code == 200
        history_items = history_res.json()["data"]
        assert len(history_items) >= 1
        assert history_items[0]["id"] == pred_data["id"]

        # 11. Verify Monitoring Overview Telemetry
        mon_res = await client.get("/api/v1/monitoring/overview", headers=headers)
        assert mon_res.status_code == 200
        mon_data = mon_res.json()["data"]
        assert mon_data["total_predictions"] >= 1
        assert mon_data["active_deployments_count"] >= 1
        assert mon_data["registered_models_count"] >= 1
