from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, Optional, Tuple

import httpx

from .base import BaseTaskHandler

logger = logging.getLogger(__name__)

_ENGINE_TRAIN_DEFAULTS: Dict[str, Dict[str, Any]] = {
    "player_clustering": {"collection": "player_features"},
    "goals_regression": {"collection": "player_statistics", "target_field": "goals"},
    "shots_regression": {"collection": "player_statistics", "target_field": "shots"},
    "goals_linear_regression": {"collection": "player_statistics", "target_field": "goals"},
    "xg_linear_regression": {"collection": "player_statistics", "target_field": "xg"},
    "position_classifier": {"collection": "player_statistics", "target_field": "position"},
    "outcome_classifier": {"collection": "matches", "target_field": "outcome"},
    "performance_anomaly_detector": {"collection": "player_statistics"},
    "tactical_role_classifier": {"collection": "player_statistics"},
    "fatigue_risk_predictor": {"collection": "player_statistics"},
    "xgot_finishing_model": {"collection": "match_events"},
    "pitch_control_nn": {"collection": "match_events"},
    "expected_threat_model": {"collection": "match_events"},
    "advanced_player_similarity": {"collection": "player_statistics"},
}

_LEGACY_TRAIN_ENDPOINTS: Dict[str, str] = {
    "player_performance": "/api/v2/ml/train/player-performance",
    "player_similarity": "/api/v2/ml/train/player-similarity",
    "xg_model": "/api/v2/ml/train/xg",
}

_LEGACY_PREDICT_ENDPOINTS: Dict[str, str] = {
    "player_performance": "/api/v2/ml/predict/player-performance",
    "match_outcome": "/api/v2/ml/predict/match-outcome",
    "xg_model": "/api/v2/ml/predict/xg",
}


class MLTaskHandler(BaseTaskHandler):
    def __init__(self, task_store, file_store, ml_service_url: str):
        super().__init__(task_store, file_store)
        self._url = ml_service_url.rstrip("/")

    @staticmethod
    def _normalize_result(
        algorithm: str,
        action: str,
        endpoint: str,
        payload: Any,
    ) -> Dict[str, Any]:
        if isinstance(payload, dict):
            data = payload.get("data", payload)
            normalized = dict(data) if isinstance(data, dict) else {"data": data}
            if "message" in payload and payload["message"]:
                normalized["message"] = payload["message"]
        else:
            normalized = {"data": payload}

        normalized.setdefault("algorithm", algorithm)
        normalized["action"] = action
        normalized["endpoint"] = endpoint
        return normalized

    @staticmethod
    def _build_engine_train_request(algorithm: str, payload: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        defaults = _ENGINE_TRAIN_DEFAULTS.get(algorithm)
        if not defaults:
            raise ValueError(f"Unsupported ML training algorithm: {algorithm}")

        body = {
            "collection": payload.get("collection") or defaults.get("collection"),
            "target_field": payload.get("target_field") or defaults.get("target_field"),
        }

        return (
            f"/api/v2/ml/engine/train/{algorithm}",
            {key: value for key, value in body.items() if value is not None},
        )

    @staticmethod
    def _resolve_similarity_predict_request(payload: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        player_id = payload.get("player_id")
        top_n = int(payload.get("top_n", 10) or 10)
        if player_id:
            return f"/api/v2/ml/similarity/player/{player_id}?top_n={top_n}", {}

        return (
            "/api/v2/ml/similarity/players",
            {
                "player_stats": payload.get("player_stats") or payload.get("input_data") or {},
                "candidate_players": payload.get("candidate_players") or [],
                "top_n": top_n,
            },
        )

    def _resolve_request(self, payload: Dict[str, Any]) -> Tuple[str, Dict[str, Any], str, str]:
        algorithm = str(payload["algorithm"])
        action = str(payload.get("action", "predict"))

        explicit_endpoint = payload.get("endpoint")
        if explicit_endpoint:
            request_body = payload.get("request_body")
            if request_body is None:
                request_body = payload.get("body") or {}
            return str(explicit_endpoint), dict(request_body), algorithm, action

        if action == "train":
            legacy_endpoint = _LEGACY_TRAIN_ENDPOINTS.get(algorithm)
            if legacy_endpoint:
                return legacy_endpoint, {}, algorithm, action

            endpoint, body = self._build_engine_train_request(algorithm, payload)
            return endpoint, body, algorithm, action

        if algorithm == "player_similarity":
            endpoint, body = self._resolve_similarity_predict_request(payload)
            return endpoint, body, algorithm, action

        legacy_predict_endpoint = _LEGACY_PREDICT_ENDPOINTS.get(algorithm)
        if legacy_predict_endpoint:
            return legacy_predict_endpoint, payload.get("input_data") or {}, algorithm, action

        if algorithm in _ENGINE_TRAIN_DEFAULTS:
            return (
                f"/api/v2/ml/engine/predict/{algorithm}",
                payload.get("input_data") or {},
                algorithm,
                action,
            )

        raise ValueError(f"Unsupported ML {action} algorithm: {algorithm}")

    async def _post_with_retries(
        self,
        client: httpx.AsyncClient,
        task_id: str,
        endpoint: str,
        request_body: Dict[str, Any],
        progress_msg: str,
    ) -> httpx.Response:
        last_error: Optional[Exception] = None

        for attempt in range(1, 4):
            try:
                if attempt > 1:
                    await self.task_store.update_progress(task_id, 10, f"{progress_msg} (retry {attempt}/3)")

                response = await client.post(f"{self._url}{endpoint}", json=request_body)
                response.raise_for_status()
                return response
            except httpx.HTTPStatusError as exc:
                detail = exc.response.text.strip()
                message = f"ml-service {exc.response.status_code} for {endpoint}"
                if detail:
                    message = f"{message}: {detail}"
                raise RuntimeError(message) from exc
            except httpx.RequestError as exc:
                last_error = exc
                if attempt == 3:
                    break
                await self.task_store.update_progress(task_id, 10, f"{progress_msg} (waiting for ml-service)")
                await asyncio.sleep(attempt)

        raise RuntimeError(f"ml-service unavailable for {endpoint}: {last_error}") from last_error

    async def execute(self, task_id: str, payload: Dict[str, Any]) -> Tuple[Optional[Dict], Optional[Dict]]:
        endpoint, request_body, algorithm, action = self._resolve_request(payload)

        async with httpx.AsyncClient(timeout=120.0) as client:
            progress_msg = f"Training {algorithm}" if action == "train" else f"Running {algorithm} prediction"
            await self.task_store.update_progress(task_id, 10, progress_msg)
            resp = await self._post_with_retries(client, task_id, endpoint, request_body, progress_msg)
            result = self._normalize_result(algorithm, action, endpoint, resp.json())

        await self.task_store.update_progress(task_id, 90, "Storing result")
        # Inline result (small) — no MinIO needed for ML outputs
        return result, None
