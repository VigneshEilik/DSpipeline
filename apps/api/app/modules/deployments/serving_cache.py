import io
import tempfile
from typing import Dict, Optional
import joblib
from ml.pipelines.inference.predictor import ChurnPredictor
from apps.api.app.infrastructure.storage import get_storage_service

class ModelServingCache:
    _loaded_predictors: Dict[str, ChurnPredictor] = {}

    @classmethod
    async def load_predictor_for_deployment(cls, deployment_id: str, artifact_path: str) -> ChurnPredictor:
        if deployment_id in cls._loaded_predictors:
            return cls._loaded_predictors[deployment_id]

        storage = get_storage_service()
        file_bytes = await storage.download_file(artifact_path)

        with tempfile.NamedTemporaryFile(suffix=".joblib", delete=False) as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name

        pipeline = joblib.load(tmp_path)
        predictor = ChurnPredictor(pipeline)
        cls._loaded_predictors[deployment_id] = predictor
        return predictor

    @classmethod
    def get_predictor(cls, deployment_id: str) -> Optional[ChurnPredictor]:
        return cls._loaded_predictors.get(deployment_id)

    @classmethod
    def evict(cls, deployment_id: str):
        cls._loaded_predictors.pop(deployment_id, None)

serving_cache = ModelServingCache
