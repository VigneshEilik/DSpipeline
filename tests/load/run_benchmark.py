import asyncio
import io
import sys
import time
sys.path.insert(0, ".")
import numpy as np
from httpx import ASGITransport, AsyncClient
from apps.api.app.main import app
from ml.pipelines.ingestion.generator import generate_telco_churn_dataset

async def benchmark_mlops_platform():
    print("==================================================================")
    print("Running ModelOps Studio Production Performance Benchmark...")
    print("==================================================================")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        from apps.api.app.main import rate_limiter
        rate_limiter.limit = 1000
        rate_limiter.requests.clear()

        # 1. Warm up & Bootstrap
        reg_res = await client.post("/api/v1/auth/bootstrap-dev")
        auth_data = reg_res.json()["data"]
        headers = {
            "Authorization": f"Bearer {auth_data['access_token']}",
            "X-Workspace-ID": auth_data["workspace_id"],
        }

        # 2. Upload dataset & train & deploy baseline model for inference benchmark
        df = generate_telco_churn_dataset(n_samples=300, random_state=42)
        csv_bytes = df.to_csv(index=False).encode("utf-8")
        up_res = await client.post(
            "/api/v1/datasets",
            headers=headers,
            data={"name": "Benchmark Dataset"},
            files={"file": ("bench.csv", io.BytesIO(csv_bytes), "text/csv")},
        )
        version_id = up_res.json()["data"]["versions"][0]["id"]

        exp_res = await client.post(
            "/api/v1/experiments",
            headers=headers,
            json={"name": "Benchmark Experiment", "dataset_version_id": version_id, "algorithm": "logistic_regression"},
        )
        exp_id = exp_res.json()["data"]["id"]
        for _ in range(25):
            await asyncio.sleep(0.3)
            poll = await client.get(f"/api/v1/experiments/{exp_id}", headers=headers)
            if poll.json()["data"]["status"] == "COMPLETED":
                break

        m_reg = await client.post(
            "/api/v1/models",
            headers=headers,
            json={"name": "Benchmark Churn Model", "experiment_id": exp_id},
        )
        model_id = m_reg.json()["data"]["id"]
        m_ver_id = m_reg.json()["data"]["latest_version"]["id"]
        await client.post(
            f"/api/v1/models/{model_id}/approve",
            headers=headers,
            json={"version_id": m_ver_id, "decision": "APPROVED", "comments": "Approved for benchmark"},
        )
        await client.post(
            "/api/v1/deployments",
            headers=headers,
            json={"name": "Benchmark Serving Deployment", "model_version_id": m_ver_id},
        )

        test_payload = {
            "features": {
                "gender": "Male",
                "tenure": 24,
                "MonthlyCharges": 65.50,
                "TotalCharges": 1572.00,
                "Contract": "One year",
                "InternetService": "DSL",
                "OnlineSecurity": "Yes",
                "TechSupport": "Yes",
                "PaymentMethod": "Bank transfer",
                "PaperlessBilling": "No",
                "SeniorCitizen": 0,
                "Partner": "Yes",
                "Dependents": "No",
                "PhoneService": "Yes",
                "MultipleLines": "No",
                "OnlineBackup": "Yes",
                "DeviceProtection": "Yes",
                "StreamingTV": "No",
                "StreamingMovies": "No",
            }
        }

        # 3. Real-Time Inference Load Benchmark (200 requests)
        n_requests = 200
        latencies = []
        errors = 0
        t0 = time.perf_counter()

        for _ in range(n_requests):
            req_start = time.perf_counter()
            res = await client.post("/api/v1/predictions", headers=headers, json=test_payload)
            req_end = time.perf_counter()
            latencies.append((req_end - req_start) * 1000)
            if res.status_code != 201:
                errors += 1

        total_duration = time.perf_counter() - t0
        rps = round(n_requests / total_duration, 2)
        p50 = round(float(np.percentile(latencies, 50)), 2)
        p95 = round(float(np.percentile(latencies, 95)), 2)
        p99 = round(float(np.percentile(latencies, 99)), 2)
        avg_lat = round(float(np.mean(latencies)), 2)

        print(f"Total Requests: {n_requests}")
        print(f"Total Time:     {total_duration:.2f}s")
        print(f"Throughput:     {rps} req/sec")
        print(f"Mean Latency:   {avg_lat} ms")
        print(f"p50 Latency:    {p50} ms")
        print(f"p95 Latency:    {p95} ms")
        print(f"p99 Latency:    {p99} ms")
        print(f"Error Rate:     {(errors / n_requests) * 100:.2f}%")

        return {
            "n_requests": n_requests,
            "total_duration": total_duration,
            "rps": rps,
            "avg_lat": avg_lat,
            "p50": p50,
            "p95": p95,
            "p99": p99,
            "errors": errors,
        }

if __name__ == "__main__":
    asyncio.run(benchmark_mlops_platform())
