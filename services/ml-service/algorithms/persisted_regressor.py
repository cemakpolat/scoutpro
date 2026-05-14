import logging
import os
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

import joblib
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.feature_extraction import DictVectorizer
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from config.settings import get_settings
from mlflow_registry import load_registered_sklearn_model, register_sklearn_model

logger = logging.getLogger(__name__)

FeatureRow = Dict[str, Any]
LabeledFeatureRows = Sequence[Tuple[FeatureRow, float]]
EstimatorFactory = Callable[[], GradientBoostingRegressor]


class PersistedDictRegressor:
    """Utility for training and persisting dict-based regressors with one-hot encoding."""

    def __init__(
        self,
        model_name: str,
        artifact_path: Optional[str] = None,
        min_samples: int = 20,
        test_size: float = 0.2,
        random_state: int = 42,
        estimator_factory: Optional[EstimatorFactory] = None,
        registry_thresholds: Optional[Dict[str, Any]] = None,
        registry_refresh_interval_seconds: int = 300,
    ):
        self.model_name = model_name
        self.min_samples = min_samples
        self.test_size = test_size
        self.random_state = random_state
        self.estimator_factory = estimator_factory or self._default_estimator
        self.artifact_path = self._resolve_artifact_path(artifact_path)
        self.registry_thresholds = registry_thresholds or {}
        self.registry_refresh_interval_seconds = registry_refresh_interval_seconds

        self.model: Optional[GradientBoostingRegressor] = None
        self.vectorizer: Optional[DictVectorizer] = None
        self.pipeline: Optional[Pipeline] = None
        self.metrics: Dict[str, Any] = {}
        self.is_fitted = False
        self.target_field: Optional[str] = None
        self.active_model_source = 'unavailable'
        self.registry_stage: Optional[str] = None
        self.registered_model_version: Optional[str] = None
        self._last_registry_refresh_at = 0.0

        if not self._load_from_registry(force=True):
            self._load_artifact()

    def _resolve_artifact_path(self, artifact_path: Optional[str]) -> Path:
        if artifact_path:
            return Path(artifact_path)

        cache_dir = os.getenv('MODEL_CACHE_DIR') or os.getenv('ML_MODEL_CACHE_DIR')
        if not cache_dir:
            cache_dir = get_settings().model_cache_dir
        return Path(cache_dir) / f'{self.model_name}.joblib'

    def _default_estimator(self) -> GradientBoostingRegressor:
        return GradientBoostingRegressor(random_state=self.random_state)

    def _build_pipeline(self) -> Optional[Pipeline]:
        if not self.model or not self.vectorizer:
            return None

        return Pipeline([
            ('vectorizer', self.vectorizer),
            ('regressor', self.model),
        ])

    def _load_from_registry(self, force: bool = False) -> bool:
        if not force and self.registry_refresh_interval_seconds > 0:
            if time.time() - self._last_registry_refresh_at < self.registry_refresh_interval_seconds:
                return self.is_fitted and self.active_model_source.startswith('mlflow:')

        self._last_registry_refresh_at = time.time()
        loaded = load_registered_sklearn_model(self.model_name)
        if not loaded:
            return False

        loaded_pipeline, metadata = loaded
        self.pipeline = loaded_pipeline
        named_steps = getattr(loaded_pipeline, 'named_steps', {})
        self.vectorizer = named_steps.get('vectorizer')
        self.model = named_steps.get('regressor')
        self.is_fitted = self.pipeline is not None
        self.registry_stage = metadata.get('registry_stage')
        self.registered_model_version = metadata.get('registered_model_version')
        self.active_model_source = metadata.get('deployment_source', 'mlflow')
        self.metrics = {
            **self.metrics,
            'model_deployment_source': self.active_model_source,
        }
        return self.is_fitted

    def _load_artifact(self) -> None:
        if not self.artifact_path.exists():
            return

        try:
            payload = joblib.load(self.artifact_path)
            self.model = payload.get('model')
            self.vectorizer = payload.get('vectorizer')
            self.pipeline = self._build_pipeline()
            self.metrics = payload.get('metrics', {})
            self.target_field = payload.get('target_field')
            self.is_fitted = bool(self.model and self.vectorizer)
            if self.is_fitted:
                self.active_model_source = 'local_artifact'
        except Exception as exc:
            logger.warning('Failed to load %s artifact from %s: %s', self.model_name, self.artifact_path, exc)
            self.model = None
            self.vectorizer = None
            self.pipeline = None
            self.metrics = {}
            self.target_field = None
            self.is_fitted = False
            self.active_model_source = 'unavailable'

    def _save_artifact(self) -> None:
        if not self.model or not self.vectorizer:
            return

        self.artifact_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(
            {
                'model': self.model,
                'vectorizer': self.vectorizer,
                'metrics': self.metrics,
                'target_field': self.target_field,
            },
            self.artifact_path,
        )

    def _register_trained_model(self) -> Dict[str, Any]:
        pipeline = self._build_pipeline()
        if pipeline is None:
            return {}

        params = {
            'target_field': self.target_field,
            'samples': self.metrics.get('samples'),
            'feature_count': self.metrics.get('feature_count'),
            'artifact_path': str(self.artifact_path),
            'trainer': type(self.model).__name__ if self.model else 'GradientBoostingRegressor',
        }
        tags = {
            'model_family': 'dict_regression',
            'model_name': self.model_name,
        }
        registration = register_sklearn_model(
            pipeline,
            model_name=self.model_name,
            params=params,
            metrics=self.metrics,
            tags=tags,
            artifact_path=self.model_name,
            run_name=f'{self.model_name}_train',
            stage_thresholds=self.registry_thresholds,
        )
        if registration.get('registry_stage') in {'Staging', 'Production'}:
            self.registry_stage = registration.get('registry_stage')
            self.registered_model_version = registration.get('registered_model_version')
        return registration

    def fit_rows(self, rows: LabeledFeatureRows, target_field: str) -> Dict[str, Any]:
        if len(rows) < self.min_samples:
            return {
                'error': f"Insufficient data ({len(rows)} samples with '{target_field}')",
                'n_samples': len(rows),
                'target_field': target_field,
            }

        feature_rows = [feature_row for feature_row, _ in rows]
        targets = [float(target) for _, target in rows]

        if len(feature_rows) >= max(12, int(1 / self.test_size)):
            X_train, X_test, y_train, y_test = train_test_split(
                feature_rows,
                targets,
                test_size=self.test_size,
                random_state=self.random_state,
            )
        else:
            X_train, X_test, y_train, y_test = feature_rows, feature_rows, targets, targets

        evaluation_vectorizer = DictVectorizer(sparse=False)
        X_train_matrix = evaluation_vectorizer.fit_transform(X_train)
        X_test_matrix = evaluation_vectorizer.transform(X_test)

        evaluation_model = self.estimator_factory()
        evaluation_model.fit(X_train_matrix, y_train)
        predictions = evaluation_model.predict(X_test_matrix)

        mae = float(mean_absolute_error(y_test, predictions))
        r2_value = float(r2_score(y_test, predictions)) if len(y_test) > 1 else 0.0

        self.vectorizer = DictVectorizer(sparse=False)
        full_matrix = self.vectorizer.fit_transform(feature_rows)
        self.model = self.estimator_factory()
        self.model.fit(full_matrix, targets)
        self.pipeline = self._build_pipeline()
        self.target_field = target_field
        self.is_fitted = True
        self.active_model_source = 'in_memory_training'
        self.metrics = {
            'status': 'success',
            'samples': len(rows),
            'target_field': target_field,
            'feature_count': len(self.vectorizer.feature_names_),
            'mae': round(mae, 4),
            'r2_score': round(r2_value, 4),
            'artifact_path': str(self.artifact_path),
            'model_deployment_source': self.active_model_source,
        }
        self._save_artifact()
        registration = self._register_trained_model()
        self.metrics.update(registration)
        return self.metrics

    def predict_value(self, feature_row: FeatureRow) -> Optional[float]:
        self._load_from_registry(force=False)

        if self.pipeline is not None:
            try:
                return float(self.pipeline.predict([feature_row])[0])
            except Exception as exc:
                logger.warning('Failed to run %s registry/local pipeline prediction: %s', self.model_name, exc)

        if not self.is_fitted or not self.model or not self.vectorizer:
            return None

        try:
            matrix = self.vectorizer.transform([feature_row])
            return float(self.model.predict(matrix)[0])
        except Exception as exc:
            logger.warning('Failed to run %s prediction: %s', self.model_name, exc)
            return None