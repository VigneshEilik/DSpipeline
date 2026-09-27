import pandas as pd
from typing import Any, Dict, List, Tuple

EXPECTED_NUMERIC_FEATURES = ["tenure", "MonthlyCharges", "TotalCharges"]
EXPECTED_CATEGORICAL_FEATURES = [
    "gender", "SeniorCitizen", "Partner", "Dependents",
    "PhoneService", "MultipleLines", "InternetService",
    "OnlineSecurity", "OnlineBackup", "DeviceProtection",
    "TechSupport", "StreamingTV", "StreamingMovies",
    "Contract", "PaperlessBilling", "PaymentMethod"
]
DEFAULT_TARGET_COLUMN = "Churn"

def validate_churn_dataset(
    df: pd.DataFrame,
    target_column: str = DEFAULT_TARGET_COLUMN,
    max_missing_ratio_threshold: float = 0.20
) -> Tuple[bool, Dict[str, Any]]:
    """
    Validates a dataset against the Telco Customer Churn schema contract.
    Returns (is_valid, validation_report_dict).
    """
    errors: List[str] = []
    warnings: List[str] = []
    column_checks: List[Dict[str, Any]] = []

    total_rows = len(df)
    total_cols = len(df.columns)

    if total_rows == 0:
        return False, {
            "status": "FAILED",
            "errors": ["Dataset is empty."],
            "warnings": [],
            "column_checks": [],
            "missing_value_summary": {},
            "class_balance_summary": {},
        }

    # 1. Target Column Check
    if target_column not in df.columns:
        errors.append(f"Target column '{target_column}' is missing from the dataset.")

    # 2. Required Features Check
    all_expected = EXPECTED_NUMERIC_FEATURES + EXPECTED_CATEGORICAL_FEATURES
    missing_expected_cols = [col for col in all_expected if col not in df.columns]
    if missing_expected_cols:
        errors.append(f"Missing expected feature columns: {', '.join(missing_expected_cols)}")

    # 3. Column-Level Inspection
    missing_value_summary: Dict[str, float] = {}
    for col in df.columns:
        missing_count = int(df[col].isna().sum())
        missing_pct = float(missing_count / total_rows)
        missing_value_summary[col] = round(missing_pct, 4)

        inferred_type = str(df[col].dtype)
        unique_count = int(df[col].nunique())

        check_info = {
            "column_name": col,
            "data_type": inferred_type,
            "missing_count": missing_count,
            "missing_percentage": missing_pct,
            "unique_values": unique_count,
        }

        if missing_pct > max_missing_ratio_threshold:
            warnings.append(
                f"Column '{col}' has a high missing value ratio: {missing_pct:.1%} (exceeds {max_missing_ratio_threshold:.0%})"
            )

        column_checks.append(check_info)

    # 4. Class Balance Summary
    class_balance_summary: Dict[str, Any] = {}
    if target_column in df.columns:
        val_counts = df[target_column].value_counts(dropna=False).to_dict()
        class_balance_summary = {str(k): int(v) for k, v in val_counts.items()}
        # Check for severe imbalance or single-class
        if len(val_counts) < 2:
            errors.append(f"Target column '{target_column}' has only 1 distinct class. Model training requires at least 2 classes.")

    status = "FAILED" if errors else ("WARNINGS" if warnings else "PASSED")
    is_valid = len(errors) == 0

    report = {
        "status": status,
        "total_rows": total_rows,
        "total_columns": total_cols,
        "is_valid": is_valid,
        "errors": errors,
        "warnings": warnings,
        "column_checks": column_checks,
        "missing_value_summary": missing_value_summary,
        "class_balance_summary": class_balance_summary,
    }

    return is_valid, report
