import numpy as np
import pandas as pd
from typing import Optional

def generate_telco_churn_dataset(
    n_samples: int = 2000,
    random_state: int = 42,
    output_path: Optional[str] = None
) -> pd.DataFrame:
    """
    Generates a realistic synthetic customer churn dataset following the Telco Churn schema.
    Features: demographics, account information, subscribed services, and Churn target.
    """
    np.random.seed(random_state)

    customer_ids = [f"CUST-{i:06d}" for i in range(1, n_samples + 1)]
    genders = np.random.choice(["Male", "Female"], size=n_samples)
    senior_citizens = np.random.choice([0, 1], size=n_samples, p=[0.84, 0.16])
    partners = np.random.choice(["Yes", "No"], size=n_samples, p=[0.48, 0.52])
    dependents = np.random.choice(["Yes", "No"], size=n_samples, p=[0.30, 0.70])

    # Tenure in months (1 to 72)
    tenures = np.random.geometric(p=0.03, size=n_samples)
    tenures = np.clip(tenures, 1, 72)

    phone_service = np.random.choice(["Yes", "No"], size=n_samples, p=[0.90, 0.10])
    multiple_lines = []
    for ps in phone_service:
        if ps == "No":
            multiple_lines.append("No phone service")
        else:
            multiple_lines.append(np.random.choice(["No", "Yes"], p=[0.52, 0.48]))

    internet_service = np.random.choice(["DSL", "Fiber optic", "No"], size=n_samples, p=[0.34, 0.44, 0.22])

    def get_service(isp, p_yes=0.35):
        if isp == "No":
            return "No internet service"
        return np.random.choice(["No", "Yes"], p=[1 - p_yes, p_yes])

    online_security = [get_service(isp, 0.28) for isp in internet_service]
    online_backup = [get_service(isp, 0.34) for isp in internet_service]
    device_protection = [get_service(isp, 0.34) for isp in internet_service]
    tech_support = [get_service(isp, 0.29) for isp in internet_service]
    streaming_tv = [get_service(isp, 0.38) for isp in internet_service]
    streaming_movies = [get_service(isp, 0.39) for isp in internet_service]

    contracts = np.random.choice(["Month-to-month", "One year", "Two year"], size=n_samples, p=[0.55, 0.21, 0.24])
    paperless_billing = np.random.choice(["Yes", "No"], size=n_samples, p=[0.59, 0.41])
    payment_methods = np.random.choice(
        [
            "Electronic check",
            "Mailed check",
            "Bank transfer (automatic)",
            "Credit card (automatic)",
        ],
        size=n_samples,
        p=[0.34, 0.23, 0.22, 0.21],
    )

    # Monthly Charges based on subscribed services
    monthly_charges = []
    for i in range(n_samples):
        charge = 20.0
        if phone_service[i] == "Yes":
            charge += 10.0
        if multiple_lines[i] == "Yes":
            charge += 10.0
        if internet_service[i] == "DSL":
            charge += 25.0
        elif internet_service[i] == "Fiber optic":
            charge += 45.0
        if online_security[i] == "Yes":
            charge += 5.0
        if online_backup[i] == "Yes":
            charge += 5.0
        if device_protection[i] == "Yes":
            charge += 5.0
        if tech_support[i] == "Yes":
            charge += 5.0
        if streaming_tv[i] == "Yes":
            charge += 10.0
        if streaming_movies[i] == "Yes":
            charge += 10.0
        charge += np.random.normal(0, 2.0)
        monthly_charges.append(round(max(18.25, charge), 2))

    monthly_charges = np.array(monthly_charges)
    total_charges = np.round(monthly_charges * tenures + np.random.normal(0, 10.0, size=n_samples), 2)
    total_charges = np.maximum(total_charges, monthly_charges)

    # Realistic Churn probability modeled on key business drivers:
    # High churn: Month-to-month contract, Fiber optic with no tech support, high monthly charges, low tenure
    churn_logits = (
        -1.5
        + (contracts == "Month-to-month") * 1.4
        - (contracts == "Two year") * 1.8
        + (internet_service == "Fiber optic") * 0.9
        - (np.array(tech_support) == "Yes") * 0.7
        - (np.array(online_security) == "Yes") * 0.6
        + (payment_methods == "Electronic check") * 0.5
        + (senior_citizens == 1) * 0.3
        - (tenures / 72.0) * 1.6
        + (monthly_charges / 100.0) * 0.8
    )

    churn_probs = 1.0 / (1.0 + np.exp(-churn_logits))
    churns = np.where(np.random.binomial(1, churn_probs) == 1, "Yes", "No")

    df = pd.DataFrame({
        "customerID": customer_ids,
        "gender": genders,
        "SeniorCitizen": senior_citizens,
        "Partner": partners,
        "Dependents": dependents,
        "tenure": tenures,
        "PhoneService": phone_service,
        "MultipleLines": multiple_lines,
        "InternetService": internet_service,
        "OnlineSecurity": online_security,
        "OnlineBackup": online_backup,
        "DeviceProtection": device_protection,
        "TechSupport": tech_support,
        "StreamingTV": streaming_tv,
        "StreamingMovies": streaming_movies,
        "Contract": contracts,
        "PaperlessBilling": paperless_billing,
        "PaymentMethod": payment_methods,
        "MonthlyCharges": monthly_charges,
        "TotalCharges": total_charges,
        "Churn": churns,
    })

    if output_path:
        df.to_csv(output_path, index=False)

    return df

if __name__ == "__main__":
    generate_telco_churn_dataset(n_samples=2500, output_path="datasets/samples/telco_churn_sample.csv")
    print("Telco churn sample dataset generated successfully.")
