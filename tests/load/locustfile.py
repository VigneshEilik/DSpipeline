import random
from locust import HttpUser, between, task

class ModelOpsUser(HttpUser):
    wait_time = between(0.1, 0.5)

    def on_start(self):
        # Bootstrap development user for load test session
        res = self.client.post("/api/v1/auth/bootstrap-dev")
        if res.status_code == 200:
            data = res.json()["data"]
            self.token = data["access_token"]
            self.workspace_id = data["workspace_id"]
            self.headers = {
                "Authorization": f"Bearer {self.token}",
                "X-Workspace-ID": self.workspace_id,
            }
        else:
            self.headers = {}

    @task(5)
    def health_check(self):
        self.client.get("/healthz")

    @task(3)
    def ready_check(self):
        self.client.get("/readyz")

    @task(10)
    def predict_churn(self):
        payload = {
            "features": {
                "gender": random.choice(["Female", "Male"]),
                "tenure": random.randint(1, 72),
                "MonthlyCharges": round(random.uniform(20.0, 115.0), 2),
                "TotalCharges": round(random.uniform(50.0, 5000.0), 2),
                "Contract": random.choice(["Month-to-month", "One year", "Two year"]),
                "InternetService": random.choice(["DSL", "Fiber optic", "No"]),
                "OnlineSecurity": random.choice(["Yes", "No", "No internet service"]),
                "TechSupport": random.choice(["Yes", "No", "No internet service"]),
                "PaymentMethod": random.choice(["Electronic check", "Mailed check", "Bank transfer", "Credit card"]),
                "PaperlessBilling": random.choice(["Yes", "No"]),
                "SeniorCitizen": random.choice([0, 1]),
                "Partner": random.choice(["Yes", "No"]),
                "Dependents": random.choice(["Yes", "No"]),
                "PhoneService": random.choice(["Yes", "No"]),
                "MultipleLines": random.choice(["Yes", "No", "No phone service"]),
                "OnlineBackup": random.choice(["Yes", "No", "No internet service"]),
                "DeviceProtection": random.choice(["Yes", "No", "No internet service"]),
                "StreamingTV": random.choice(["Yes", "No", "No internet service"]),
                "StreamingMovies": random.choice(["Yes", "No", "No internet service"]),
            }
        }
        self.client.post("/api/v1/predictions", headers=self.headers, json=payload)
