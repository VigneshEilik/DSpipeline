from pathlib import Path
from typing import Any, Dict, List, Union
import joblib
import pandas as pd
from sklearn.pipeline import Pipeline

class ChurnPredictor:
    def __init__(self, model_pipeline: Union[Pipeline, str, Path]):
        if isinstance(model_pipeline, (str, Path)):
            self.pipeline: Pipeline = joblib.load(str(model_pipeline))
        else:
            self.pipeline = model_pipeline

    def predict_single(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes real-time inference on a single customer feature dictionary.
        Returns:
            - prediction_label ("Yes" or "No")
            - prediction_probability (float 0.0 - 1.0)
            - risk_category ("Low", "Medium", "High")
        """
        df = pd.DataFrame([features])
        prob = float(self.pipeline.predict_proba(df)[0, 1])
        label = "Yes" if prob >= 0.50 else "No"

        if prob >= 0.65:
            risk = "High"
        elif prob >= 0.35:
            risk = "Medium"
        else:
            risk = "Low"

        return {
            "prediction_label": label,
            "prediction_probability": round(prob, 4),
            "risk_category": risk,
        }

    def predict_batch(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Executes batch inference on a pandas DataFrame.
        Adds churn_probability, churn_prediction, and risk_category columns.
        """
        probs = self.pipeline.predict_proba(df)[:, 1]
        results_df = df.copy()
        results_df["churn_probability"] = np.round(probs, 4)
        results_df["churn_prediction"] = np.where(probs >= 0.50, "Yes", "No")

        conditions = [
            (probs >= 0.65),
            (probs >= 0.35) & (probs < 0.65),
            (probs < 0.35),
        ]
        choices = ["High", "Medium", "Low"]
        results_df["risk_category"] = np.select(conditions, choices, default="Medium")

        return results_df

import numpy as np
