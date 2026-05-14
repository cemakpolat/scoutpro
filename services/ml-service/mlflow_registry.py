import logging
from typing import Any, Dict, Optional, Sequence, Tuple

from config.settings import get_settings

logger = logging.getLogger(__name__)


def _configure_mlflow():
    import mlflow

    settings = get_settings()
    mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
    mlflow.set_experiment(settings.mlflow_experiment_name)
    return mlflow


def determine_registry_stage(
    metrics: Dict[str, Any],
    staging_min_r2: float = 0.35,
    production_min_r2: float = 0.6,
) -> str:
    try:
        r2_value = float(metrics.get('r2_score', 0.0) or 0.0)
    except (TypeError, ValueError):
        return 'None'

    if r2_value >= production_min_r2:
        return 'Production'
    if r2_value >= staging_min_r2:
        return 'Staging'
    return 'None'


def register_sklearn_model(
    model: Any,
    model_name: str,
    params: Optional[Dict[str, Any]] = None,
    metrics: Optional[Dict[str, Any]] = None,
    tags: Optional[Dict[str, Any]] = None,
    artifact_path: Optional[str] = None,
    run_name: Optional[str] = None,
    stage_thresholds: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    params = params or {}
    metrics = metrics or {}
    tags = tags or {}

    try:
        mlflow = _configure_mlflow()
        import mlflow.sklearn

        clean_params = {
            key: value
            for key, value in params.items()
            if value not in (None, '')
        }
        clean_metrics = {}
        for key, value in metrics.items():
            try:
                clean_metrics[key] = float(value)
            except (TypeError, ValueError):
                continue

        with mlflow.start_run(run_name=run_name or f'{model_name}_train') as run:
            for key, value in tags.items():
                if value not in (None, ''):
                    mlflow.set_tag(key, str(value))
            if clean_params:
                mlflow.log_params(clean_params)
            if clean_metrics:
                mlflow.log_metrics(clean_metrics)

            mlflow.sklearn.log_model(
                model,
                artifact_path=artifact_path or model_name,
                registered_model_name=model_name,
            )

            result = {
                'mlflow_run_id': run.info.run_id,
            }

        client = mlflow.tracking.MlflowClient()
        stage = determine_registry_stage(metrics, **(stage_thresholds or {}))
        result['registry_stage'] = stage

        unassigned_versions = client.get_latest_versions(model_name, stages=['None'])
        if unassigned_versions:
            latest_version = sorted(unassigned_versions, key=lambda item: int(item.version))[-1]
            result['registered_model_version'] = str(latest_version.version)
            if stage in {'Staging', 'Production'}:
                client.transition_model_version_stage(
                    name=model_name,
                    version=latest_version.version,
                    stage=stage,
                    archive_existing_versions=stage == 'Production',
                )

        return result
    except Exception as exc:
        logger.warning('MLflow registration skipped for %s: %s', model_name, exc)
        return {
            'mlflow_skipped': str(exc),
            'registry_stage': 'registration_skipped',
        }


def load_registered_sklearn_model(
    model_name: str,
    prefer_stages: Sequence[str] = ('Production', 'Staging'),
) -> Optional[Tuple[Any, Dict[str, Any]]]:
    try:
        mlflow = _configure_mlflow()
        import mlflow.sklearn

        client = mlflow.tracking.MlflowClient()
        for stage in prefer_stages:
            versions = client.get_latest_versions(model_name, stages=[stage])
            if not versions:
                continue

            latest_version = sorted(versions, key=lambda item: int(item.version))[-1]
            loaded_model = mlflow.sklearn.load_model(f'models:/{model_name}/{stage}')
            return loaded_model, {
                'registry_stage': stage,
                'registered_model_version': str(latest_version.version),
                'deployment_source': f'mlflow:{stage}',
            }
    except Exception as exc:
        logger.warning('MLflow registry load skipped for %s: %s', model_name, exc)

    return None