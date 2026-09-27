# ADR 0002: Unified Preprocessing and Model Pipeline Serialization

## Status
Accepted

## Context
A major cause of silent failures in production machine learning systems is train/serve skew: when data preprocessing applied during model training diverges from the preprocessing applied during live inference, or when features are computed differently. Additionally, fitting encoders or imputers on the full dataset before splitting leads to data leakage and invalid metrics.

## Decision
1. All feature transformations (numerical imputation, standard scaling, categorical imputation, and one-hot encoding) are encapsulated within a `scikit-learn` `ColumnTransformer`.
2. The preprocessor and the estimator are bundled into a single `Pipeline(steps=[('preprocessor', preprocessor), ('classifier', estimator)])`.
3. The pipeline is strictly fitted on the training split only (`pipeline.fit(X_train, y_train)`).
4. The entire fitted pipeline is serialized as a single atomic artifact using `joblib`.
5. Inference endpoints load this single artifact and call `pipeline.predict_proba(input_df)` directly on raw feature inputs.

## Consequences
- **Positive**: 100% elimination of train/serve skew; inference never requires custom ad-hoc preprocessing functions; impossible for preprocessing logic to drift between training and serving.
- **Negative**: Artifact file size includes both preprocessor transformers and model weights; strict compatibility of `scikit-learn` versions between training and inference environments must be maintained.
