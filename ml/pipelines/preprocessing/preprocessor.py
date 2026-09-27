from typing import List
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from ml.pipelines.validation.validator import (
    EXPECTED_CATEGORICAL_FEATURES,
    EXPECTED_NUMERIC_FEATURES,
)

def create_preprocessing_pipeline(
    numeric_features: List[str] = EXPECTED_NUMERIC_FEATURES,
    categorical_features: List[str] = EXPECTED_CATEGORICAL_FEATURES,
) -> ColumnTransformer:
    """
    Creates a scikit-learn ColumnTransformer for customer churn tabular data.
    - Numeric features: Median imputation + Standard scaling
    - Categorical features: Constant imputation + OneHotEncoding (handle_unknown='ignore')
    """
    numeric_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )

    categorical_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="constant", fill_value="Missing")),
            ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, numeric_features),
            ("cat", categorical_transformer, categorical_features),
        ],
        remainder="drop",
    )

    return preprocessor
