import os
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    auc,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from ml.pipelines.preprocessing.preprocessor import create_preprocessing_pipeline
from ml.pipelines.validation.validator import (
    DEFAULT_TARGET_COLUMN,
    EXPECTED_CATEGORICAL_FEATURES,
    EXPECTED_NUMERIC_FEATURES,
)

SUPPORTED_ALGORITHMS = {
    "logistic_regression": LogisticRegression,
    "random_forest": RandomForestClassifier,
    "hist_gradient_boosting": HistGradientBoostingClassifier,
}

def get_classifier(algorithm: str, hyperparameters: Dict[str, Any], random_seed: int = 42):
    params = hyperparameters.copy()
    if algorithm == "logistic_regression":
        params.setdefault("max_iter", 1000)
        params.setdefault("class_weight", "balanced")
        params.setdefault("random_state", random_seed)
        return LogisticRegression(**params)
    elif algorithm == "random_forest":
        params.setdefault("n_estimators", 100)
        params.setdefault("class_weight", "balanced")
        params.setdefault("random_state", random_seed)
        return RandomForestClassifier(**params)
    elif algorithm == "hist_gradient_boosting":
        params.setdefault("random_state", random_seed)
        params.setdefault("class_weight", "balanced")
        return HistGradientBoostingClassifier(**params)
    else:
        raise ValueError(f"Unsupported algorithm '{algorithm}'. Supported: {list(SUPPORTED_ALGORITHMS.keys())}")

def train_churn_model(
    df: pd.DataFrame,
    algorithm: str = "logistic_regression",
    hyperparameters: Optional[Dict[str, Any]] = None,
    test_size: float = 0.20,
    random_seed: int = 42,
    target_column: str = DEFAULT_TARGET_COLUMN,
    artifact_output_dir: Optional[str] = None,
) -> Tuple[Pipeline, Dict[str, Any]]:
    """
    Trains a reproducible churn prediction model with zero train/serve skew.
    - Fits preprocessing on training split only.
    - Evaluates on untouched test split.
    - Serializes complete Pipeline (preprocessor + model) into an atomic joblib artifact.
    """
    start_time = time.time()
    hyperparams = hyperparameters or {}

    feature_cols = EXPECTED_NUMERIC_FEATURES + EXPECTED_CATEGORICAL_FEATURES
    X = df[feature_cols].copy()

    # Convert binary churn target to 1/0
    y_raw = df[target_column]
    if y_raw.dtype == object or str(y_raw.iloc[0]).lower() in ["yes", "no"]:
        y = (y_raw.astype(str).str.strip().str.lower() == "yes").astype(int)
    else:
        y = y_raw.astype(int)

    # 1. Stratified Train/Test Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_seed, stratify=y
    )

    # 2. Build Unified Pipeline
    preprocessor = create_preprocessing_pipeline()
    classifier = get_classifier(algorithm, hyperparams, random_seed=random_seed)

    pipeline = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("classifier", classifier),
        ]
    )

    # 3. Fit Pipeline on Training Data Only
    pipeline.fit(X_train, y_train)

    # 4. Evaluate on Untouched Test Set
    y_pred = pipeline.predict(X_test)
    y_prob = None
    if hasattr(pipeline, "predict_proba"):
        y_prob = pipeline.predict_proba(X_test)[:, 1]

    # Calculate Metrics
    acc = float(accuracy_score(y_test, y_pred))
    prec = float(precision_score(y_test, y_pred, zero_division=0))
    rec = float(recall_score(y_test, y_pred, zero_division=0))
    f1 = float(f1_score(y_test, y_pred, zero_division=0))

    roc_auc = None
    pr_auc = None
    if y_prob is not None:
        roc_auc = float(roc_auc_score(y_test, y_prob))
        precision_curve, recall_curve, _ = precision_recall_curve(y_test, y_prob)
        pr_auc = float(auc(recall_curve, precision_curve))

    cm = confusion_matrix(y_test, y_pred).tolist()
    clf_report = classification_report(y_test, y_pred, output_dict=True, zero_division=0)

    # Feature Importance (if tree-based model)
    feature_importances = {}
    clf = pipeline.named_steps["classifier"]
    if hasattr(clf, "feature_importances_"):
        try:
            onehot_cols = pipeline.named_steps["preprocessor"].transformers_[1][1].named_steps["onehot"].get_feature_names_out(EXPECTED_CATEGORICAL_FEATURES)
            all_encoded_features = EXPECTED_NUMERIC_FEATURES + list(onehot_cols)
            importances = clf.feature_importances_
            feature_importances = {
                feat: round(float(imp), 4)
                for feat, imp in sorted(zip(all_encoded_features, importances), key=lambda x: x[1], reverse=True)[:15]
            }
        except Exception:
            feature_importances = {}

    duration = round(time.time() - start_time, 2)

    # 5. Serialize Artifact
    artifact_path = None
    if artifact_output_dir:
        out_dir = Path(artifact_output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{algorithm}_seed{random_seed}_{int(time.time())}.joblib"
        artifact_path = str(out_dir / filename)
        joblib.dump(pipeline, artifact_path)

    metrics = {
        "accuracy": round(acc, 4),
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "f1_score": round(f1, 4),
        "roc_auc": round(roc_auc, 4) if roc_auc is not None else None,
        "pr_auc": round(pr_auc, 4) if pr_auc is not None else None,
        "confusion_matrix": cm,
        "classification_report": clf_report,
        "feature_importances": feature_importances,
        "duration_seconds": duration,
        "algorithm": algorithm,
        "hyperparameters": hyperparams,
        "random_seed": random_seed,
        "test_samples": len(X_test),
        "train_samples": len(X_train),
        "artifact_path": artifact_path,
    }

    return pipeline, metrics
