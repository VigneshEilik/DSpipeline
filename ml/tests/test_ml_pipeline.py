import os
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

from ml.pipelines.ingestion.generator import generate_telco_churn_dataset
from ml.pipelines.validation.validator import validate_churn_dataset
from ml.pipelines.training.trainer import train_churn_model
from ml.pipelines.inference.predictor import ChurnPredictor

@pytest.fixture
def sample_dataset():
    return generate_telco_churn_dataset(n_samples=200, random_state=42)

def test_dataset_validation_success(sample_dataset):
    is_valid, report = validate_churn_dataset(sample_dataset)
    assert is_valid is True
    assert report["status"] in ["PASSED", "WARNINGS"]
    assert report["total_rows"] == 200
    assert len(report["errors"]) == 0
    assert "class_balance_summary" in report

def test_dataset_validation_missing_target(sample_dataset):
    bad_df = sample_dataset.drop(columns=["Churn"])
    is_valid, report = validate_churn_dataset(bad_df)
    assert is_valid is False
    assert report["status"] == "FAILED"
    assert any("Target column" in err for err in report["errors"])

def test_model_training_and_serialization(sample_dataset, tmp_path):
    pipeline, metrics = train_churn_model(
        df=sample_dataset,
        algorithm="logistic_regression",
        random_seed=42,
        test_size=0.25,
        artifact_output_dir=str(tmp_path),
    )

    # Verify metrics structure
    assert 0.0 <= metrics["accuracy"] <= 1.0
    assert 0.0 <= metrics["precision"] <= 1.0
    assert 0.0 <= metrics["recall"] <= 1.0
    assert 0.0 <= metrics["f1_score"] <= 1.0
    assert metrics["roc_auc"] is not None and 0.0 <= metrics["roc_auc"] <= 1.0
    assert len(metrics["confusion_matrix"]) == 2
    assert Path(metrics["artifact_path"]).exists()

    # Verify Predictor can load the saved artifact directly
    predictor = ChurnPredictor(metrics["artifact_path"])

    # Single inference test
    single_record = sample_dataset.iloc[0].drop("Churn").to_dict()
    res = predictor.predict_single(single_record)

    assert res["prediction_label"] in ["Yes", "No"]
    assert 0.0 <= res["prediction_probability"] <= 1.0
    assert res["risk_category"] in ["Low", "Medium", "High"]

    # Batch inference test
    batch_df = sample_dataset.drop(columns=["Churn"]).head(10)
    batch_res = predictor.predict_batch(batch_df)
    assert len(batch_res) == 10
    assert "churn_probability" in batch_res.columns
    assert "churn_prediction" in batch_res.columns
    assert "risk_category" in batch_res.columns

def test_multi_algorithm_training(sample_dataset, tmp_path):
    for algo in ["random_forest", "hist_gradient_boosting"]:
        pipeline, metrics = train_churn_model(
            df=sample_dataset,
            algorithm=algo,
            random_seed=42,
            test_size=0.25,
            artifact_output_dir=str(tmp_path),
        )
        assert metrics["accuracy"] > 0.50
        assert metrics["algorithm"] == algo
