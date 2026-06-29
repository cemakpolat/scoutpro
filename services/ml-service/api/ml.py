"""
ML API Endpoints
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional
import logging
import os
import sys
sys.path.append('/app')
from shared.models.base import APIResponse
from models.predictor import (
    PlayerPerformancePredictor,
    MatchOutcomePredictor,
    PlayerSimilarityFinder,
    XGModel,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2/ml", tags=["machine-learning"])

# Initialize traditional predictors (compatibility)
player_predictor = PlayerPerformancePredictor()
match_predictor = MatchOutcomePredictor()
similarity_finder = PlayerSimilarityFinder()

# XG model singleton
_xg_model: Optional[XGModel] = None

def get_xg_model() -> XGModel:
    global _xg_model
    if _xg_model is None:
        _xg_model = XGModel()
    return _xg_model

# Initialize Clean Architecture Analytics Engine (singleton)

from api.form import router as form_router
router.include_router(form_router)

from engine import AnalyticsEngine
import time
from datetime import datetime

_trajectory_cache = {}
_TRAJECTORY_CACHE_TTL = 3600  # 1 hour

from config.settings import get_settings as _get_settings

_engine: Optional[AnalyticsEngine] = None

def get_engine() -> AnalyticsEngine:
    global _engine
    if _engine is None:
        _engine = AnalyticsEngine()
    return _engine

@router.get("/engine/algorithms", response_model=APIResponse)
async def list_engine_algorithms():
    """Return all registered AnalyticsEngine algorithms and their fit status."""
    try:
        algorithms = get_engine().get_registered_algorithms()
        return APIResponse(success=True, data=algorithms, message=f"{len(algorithms)} algorithms registered")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/engine/train/{algorithm_name}", response_model=APIResponse)
async def train_with_engine(algorithm_name: str, body: Dict[str, Any]):
    """Train a named algorithm from MongoDB. Body: {collection, target_field (optional)}."""
    try:
        settings = _get_settings()
        collection = body.get("collection", "player_statistics")
        target_field = body.get("target_field") or None
        result = get_engine().train_from_mongo(
            algorithm_name,
            settings.mongodb_url,
            collection=collection,
            target_field=target_field,
        )
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        return APIResponse(
            success=True,
            data={"algorithm": algorithm_name, **result},
            message=f"Training complete for {algorithm_name}",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

_NOT_FITTED_PHRASES = ("not fitted", "is not fitted", "needs at least", "insufficient data")

_ALGORITHM_COLLECTION_MAP = {
    "tactical_role_classifier": "player_statistics",
    "performance_anomaly_detector": "player_statistics",
    "fatigue_risk_predictor": "player_statistics",
    "market_value_estimator": "player_statistics",
    "vaep_action_model": "match_events",
}

def _is_not_fitted_error(prediction: Dict[str, Any]) -> bool:
    msg = str(prediction.get("error", "")).lower()
    return any(phrase in msg for phrase in _NOT_FITTED_PHRASES)


def _parse_date_value(value: Any) -> Optional[datetime]:
    if value in (None, '', 'None'):
        return None
    text = str(value).replace('Z', '+00:00')
    for candidate in (text, text.replace(' ', 'T')):
        try:
            parsed = datetime.fromisoformat(candidate)
            return parsed.replace(tzinfo=None) if parsed.tzinfo is not None else parsed
        except ValueError:
            continue
    return None


def _derive_age_from_player(player: Dict[str, Any]) -> Optional[int]:
    raw_age = player.get('age')
    if raw_age not in (None, '', 'None'):
        try:
            return int(raw_age)
        except (TypeError, ValueError):
            pass

    parsed_birth_date = _parse_date_value(
        player.get('birth_date')
        or player.get('birthDate')
        or player.get('date_of_birth')
    )
    if not parsed_birth_date:
        return None

    today = datetime.utcnow()
    age = today.year - parsed_birth_date.year - ((today.month, today.day) < (parsed_birth_date.month, parsed_birth_date.day))
    return age if age >= 0 else None


def _estimate_contract_years_remaining(player: Dict[str, Any]) -> float:
    contract = player.get('contract') if isinstance(player.get('contract'), dict) else {}
    expiry_value = (
        player.get('contractExpiry')
        or player.get('contract_expiry')
        or player.get('contractEnd')
        or player.get('contract_end')
        or contract.get('expiryDate')
    )
    parsed_expiry = _parse_date_value(expiry_value)
    if not parsed_expiry:
        return 2.0

    delta_days = (parsed_expiry.date() - datetime.utcnow().date()).days
    return round(max(0.0, delta_days / 365.25), 2)


def _player_candidate_ids(player_id: str, player: Dict[str, Any]) -> List[str]:
    candidates: List[str] = []

    def add(candidate: Any) -> None:
        if candidate in (None, '', 'None'):
            return
        normalized = str(candidate).strip()
        if normalized and normalized not in candidates:
            candidates.append(normalized)

    add(player_id)
    provider_ids = player.get('provider_ids') or {}
    if isinstance(provider_ids, dict):
        add(provider_ids.get('opta'))
    add(player.get('uID'))
    add(player.get('player_id'))
    add(player.get('id'))
    return candidates


def _stat_value(stats: Dict[str, Any], *keys: str) -> float:
    for key in keys:
        value = stats.get(key)
        if value in (None, '', 'None'):
            continue
        try:
            return float(value)
        except (TypeError, ValueError):
            continue
    return 0.0


def _stat_pass_accuracy(stats: Dict[str, Any]) -> float:
    direct = _stat_value(stats, 'pass_accuracy', 'passAccuracy')
    if direct:
        return round(direct, 2)

    accurate = _stat_value(stats, 'accurate_pass')
    total = _stat_value(stats, 'total_pass')
    return round(accurate / total * 100.0, 2) if total > 0 else 0.0

@router.post("/engine/predict/{algorithm_name}", response_model=APIResponse)
async def predict_with_engine(algorithm_name: str, input_data: Dict[str, Any]):
    """Run inference using the AnalyticsEngine. Body: arbitrary feature dict."""
    try:
        engine = get_engine()
        prediction = engine.predict(algorithm_name, input_data)

        if isinstance(prediction, dict) and "error" in prediction:
            error_msg = str(prediction["error"])

            if _is_not_fitted_error(prediction):
                # Keep predictions non-blocking: training is handled asynchronously by task workers.
                return APIResponse(
                    success=False,
                    data={"algorithm": algorithm_name, "available": False, "reason": error_msg},
                    message=f"{algorithm_name} is not fitted yet. Queue a training task and retry.",
                )

            raise HTTPException(status_code=400, detail=error_msg)

        return APIResponse(
            success=True,
            data={"algorithm": algorithm_name, "prediction": prediction},
            message=f"Prediction successful for {algorithm_name}",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@router.post("/predict/player-performance", response_model=APIResponse)
async def predict_player_performance(features: Dict[str, Any]):
    """Predict player performance based on features"""
    try:
        prediction = player_predictor.predict(features)

        return APIResponse(
            success=True,
            data=prediction,
            message="Player performance predicted"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/predict/match-outcome", response_model=APIResponse)
async def predict_match_outcome(features: Dict[str, Any]):
    """Predict match outcome"""
    try:
        prediction = match_predictor.predict(features)

        return APIResponse(
            success=True,
            data=prediction,
            message="Match outcome predicted"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/similarity/players", response_model=APIResponse)
async def find_similar_players(
    player_stats: Dict[str, Any],
    candidate_players: List[Dict[str, Any]],
    top_n: int = 10
):
    """Find similar players"""
    try:
        similar = similarity_finder.find_similar_players(
            player_stats,
            candidate_players,
            top_n
        )

        return APIResponse(
            success=True,
            data=similar,
            message=f"Found {len(similar)} similar players"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models", response_model=APIResponse)
async def list_models():
    """List available ML models"""
    models = [
        {
            "name": "player_performance",
            "type": "regression",
            "status": "active"
        },
        {
            "name": "match_outcome",
            "type": "classification",
            "status": "active"
        },
        {
            "name": "player_similarity",
            "type": "similarity",
            "status": "active"
        }
    ]

    # Append Engine algorithms dynamically
    from .ml import get_engine
    engine_algs = get_engine().algorithms.keys()
    for alg in engine_algs:
        models.append({
            "name": alg,
            "type": "engine_algorithm",
            "status": "active"
        })

    return APIResponse(
        success=True,
        data=models,
        message=f"Retrieved {len(models)} models"
    )


# ---------------------------------------------------------------------------
# Feature store status
# ---------------------------------------------------------------------------

@router.get("/features/status", response_model=APIResponse)
async def get_features_status():
    """Return count of documents in the player_features collection."""
    url = os.getenv("MONGODB_URL", "mongodb://root:scoutpro123@mongo:27017/scoutpro")
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        client = AsyncIOMotorClient(url, serverSelectionTimeoutMS=5000)
        db = client.get_default_database()
        count = await db["player_features"].count_documents({})
        client.close()
        return APIResponse(
            success=True,
            data={"player_features_count": count},
            message="Feature store status retrieved",
        )
    except Exception as e:
        logger.error(f"Features status check failed: {e}")
        return APIResponse(
            success=False,
            data={"player_features_count": 0},
            message=str(e),
        )


# ---------------------------------------------------------------------------
# Training endpoints
# ---------------------------------------------------------------------------

@router.post("/train/player-performance", response_model=APIResponse)
async def train_player_performance():
    """
    Load all player_features, fit GradientBoostingRegressor, save to
    /models/player_performance.pkl, and log metrics to MLflow.
    """
    import numpy as np
    import pandas as pd
    from sklearn.ensemble import GradientBoostingRegressor
    import joblib
    from motor.motor_asyncio import AsyncIOMotorClient

    url = os.getenv("MONGODB_URL", "mongodb://root:scoutpro123@mongo:27017/scoutpro")
    feature_cols = ["pass_accuracy", "shot_accuracy", "duel_win_rate", "matches_played"]

    try:
        client = AsyncIOMotorClient(url, serverSelectionTimeoutMS=5000)
        db = client.get_default_database()
        docs = await db["player_features"].find({}).to_list(length=None)
        client.close()

        if len(docs) < 2:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient data: only {len(docs)} player_features docs (need >= 2). "
                       "Call /features/status and bootstrap first.",
            )

        df = pd.DataFrame(docs)
        for col in feature_cols:
            if col not in df.columns:
                df[col] = 0.0

        X = df[feature_cols].fillna(0.0).values
        # Synthetic performance rating as training target
        y = (df["pass_accuracy"].fillna(0) * 0.35 +
             df["shot_accuracy"].fillna(0) * 0.40 +
             df["duel_win_rate"].fillna(0) * 0.25).values

        model = GradientBoostingRegressor(n_estimators=100, random_state=42)
        model.fit(X, y)
        train_score = float(model.score(X, y))

        os.makedirs("/models", exist_ok=True)
        joblib.dump({"model": model, "feature_cols": feature_cols},
                    "/models/player_performance.pkl")

        # Refresh the in-process predictor instance
        player_predictor.model = model
        player_predictor.is_fitted = True
        player_predictor.feature_cols = feature_cols

        # Log to MLflow (best-effort)
        try:
            import mlflow
            with mlflow.start_run(run_name="player_performance"):
                mlflow.log_param("n_estimators", 100)
                mlflow.log_param("n_samples", len(X))
                mlflow.log_metric("train_r2", train_score)
        except Exception as mlf_e:
            logger.warning(f"MLflow logging skipped: {mlf_e}")

        return APIResponse(
            success=True,
            data={"n_samples": len(X), "train_r2": train_score},
            message="PlayerPerformancePredictor trained and saved",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Player performance training failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/train/player-similarity", response_model=APIResponse)
async def train_player_similarity():
    """
    Load all player_features, fit KMeans(n_clusters=5), save to
    /models/player_similarity.pkl, and log metrics to MLflow.
    """
    import numpy as np
    import pandas as pd
    from sklearn.cluster import KMeans
    import joblib
    from motor.motor_asyncio import AsyncIOMotorClient

    url = os.getenv("MONGODB_URL", "mongodb://root:scoutpro123@mongo:27017/scoutpro")
    feature_cols = ["pass_accuracy", "shot_accuracy", "duel_win_rate", "matches_played"]

    try:
        client = AsyncIOMotorClient(url, serverSelectionTimeoutMS=5000)
        db = client.get_default_database()
        docs = await db["player_features"].find({}).to_list(length=None)
        client.close()

        if len(docs) < 5:
            raise HTTPException(
                status_code=400,
                detail=f"Need at least 5 player_features docs for clustering (found {len(docs)}).",
            )

        df = pd.DataFrame(docs)
        for col in feature_cols:
            if col not in df.columns:
                df[col] = 0.0

        X = df[feature_cols].fillna(0.0).values
        n_clusters = min(5, len(X))

        model = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        model.fit(X)

        os.makedirs("/models", exist_ok=True)
        joblib.dump({"model": model, "feature_cols": feature_cols},
                    "/models/player_similarity.pkl")

        # Log to MLflow (best-effort)
        try:
            import mlflow
            with mlflow.start_run(run_name="player_similarity"):
                mlflow.log_param("n_clusters", n_clusters)
                mlflow.log_param("n_samples", len(X))
                mlflow.log_metric("inertia", float(model.inertia_))
        except Exception as mlf_e:
            logger.warning(f"MLflow logging skipped: {mlf_e}")

        return APIResponse(
            success=True,
            data={"n_samples": len(X), "n_clusters": n_clusters,
                  "inertia": float(model.inertia_)},
            message="PlayerSimilarity KMeans model trained and saved",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Player similarity training failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Similarity by player ID (MongoDB-backed cosine similarity)
# ---------------------------------------------------------------------------

@router.get("/similarity/player/{player_id}", response_model=APIResponse)
async def find_similar_players_by_id(player_id: str, top_n: int = 10):
    """Find the top_n most similar players to player_id using cosine similarity on player_features."""
    try:
        similar = await similarity_finder.find_similar_by_id(player_id, top_n)
        return APIResponse(
            success=True,
            data=similar,
            message=f"Found {len(similar)} similar players for {player_id}",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# xG (Expected Goals) endpoints
# ---------------------------------------------------------------------------

@router.post("/train/xg", response_model=APIResponse)
async def train_xg_model():
    """Train the xG logistic regression model from match_events in MongoDB."""
    import asyncio
    url = os.getenv("MONGODB_URL", "mongodb://root:scoutpro123@mongo:27017/scoutpro")
    try:
        xg_model = get_xg_model()
        loop = asyncio.get_event_loop()
        metrics = await loop.run_in_executor(None, xg_model.train_from_mongo, url)
        if "error" in metrics:
            raise HTTPException(status_code=400, detail=metrics["error"])
        return APIResponse(
            success=True,
            data=metrics,
            message="xG model trained successfully",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"xG training failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/predict/xg", response_model=APIResponse)
async def predict_xg(shot: Dict[str, Any]):
    """Predict xG for a single shot event document.

    Body example::

        {"location": {"x": 85, "y": 45}, "raw_event": {"body_part": "right_foot",
        "shot_type": "open_play"}, "qualifiers": {"102": "55", "103": "40"}}
    """
    try:
        xg_model = get_xg_model()
        xg_value = xg_model.predict_xg(shot)
        return APIResponse(
            success=True,
            data={"xg": xg_value},
            message="xG predicted",
        )
    except Exception as e:
        logger.error(f"xG prediction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/xg/status", response_model=APIResponse)
async def xg_model_status():
    """Return xG model status: whether it is fitted and whether the model file exists."""
    try:
        xg_model = get_xg_model()
        return APIResponse(
            success=True,
            data={
                "fitted": xg_model.is_fitted,
                "model_path": xg_model.model_path,
                "exists": os.path.exists(xg_model.model_path),
            },
            message="xG model status retrieved",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/players/{player_id}/market-value", response_model=APIResponse)
async def get_player_market_value(player_id: str):
    """Estimate a player's market value from canonical player and statistics documents."""
    url = os.getenv("MONGODB_URL", "mongodb://root:scoutpro123@mongo:27017/scoutpro")

    try:
        from motor.motor_asyncio import AsyncIOMotorClient

        client = AsyncIOMotorClient(url, serverSelectionTimeoutMS=5000)
        db = client.get_default_database()

        player_lookup_values: List[Any] = [player_id]
        if player_id.isdigit():
            player_lookup_values.append(int(player_id))

        player = await db["players"].find_one(
            {
                "$or": [
                    {"id": {"$in": player_lookup_values}},
                    {"player_id": {"$in": player_lookup_values}},
                    {"uID": {"$in": player_lookup_values}},
                    {"provider_ids.opta": {"$in": player_lookup_values}},
                ]
            },
            {"_id": 0},
        )

        if not player:
            client.close()
            raise HTTPException(status_code=404, detail=f"Player {player_id} not found")

        stats: Dict[str, Any] = {}
        for candidate in _player_candidate_ids(player_id, player):
            stats_lookup_values: List[Any] = [candidate]
            if candidate.isdigit():
                stats_lookup_values.append(int(candidate))
            stats = await db["player_statistics"].find_one(
                {
                    "$or": [
                        {"playerID": {"$in": stats_lookup_values}},
                        {"player_id": {"$in": stats_lookup_values}},
                        {"playerId": {"$in": stats_lookup_values}},
                    ]
                },
                {"_id": 0},
            ) or {}
            if stats:
                break

        client.close()

        features = {
            'player_id': player_id,
            'player_name': player.get('name'),
            'position': player.get('position') or player.get('detailed_position') or player.get('detailedPosition'),
            'age': _derive_age_from_player(player),
            'minutes_played': _stat_value(stats, 'minutes_played'),
            'matches_played': _stat_value(stats, 'matches_played', 'games_played', 'appearances'),
            'goals': _stat_value(stats, 'goals'),
            'assists': _stat_value(stats, 'goal_assist', 'assists'),
            'total_xg': _stat_value(stats, 'total_xg', 'xg_total'),
            'progressive_passes': _stat_value(stats, 'progressive_passes'),
            'key_passes': _stat_value(stats, 'key_passes'),
            'pressures': _stat_value(stats, 'pressures'),
            'tackles': _stat_value(stats, 'tackles', 'total_tackles'),
            'interceptions': _stat_value(stats, 'interceptions', 'total_interceptions'),
            'pass_accuracy': _stat_pass_accuracy(stats),
            'contract_years_remaining': _estimate_contract_years_remaining(player),
        }
        prediction = get_engine().predict('market_value_estimator', features)
        if isinstance(prediction, dict) and 'error' in prediction:
            raise HTTPException(status_code=400, detail=prediction['error'])

        return APIResponse(
            success=True,
            data={
                **prediction,
                'player_id': player_id,
                'player_name': player.get('name'),
                'position': features['position'],
            },
            message='Player market value estimated',
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Market value estimation failed for player {player_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models/registry", response_model=APIResponse)
async def get_model_registry():
    """List all registered models in MLflow with their current stage and version."""
    try:
        import mlflow
        settings = get_settings()
        mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
        client = mlflow.tracking.MlflowClient()
        models = []
        for rm in client.search_registered_models():
            latest = client.get_latest_versions(rm.name)
            models.append({
                "name": rm.name,
                "versions": [
                    {
                        "version": v.version,
                        "stage": v.current_stage,
                        "run_id": v.run_id,
                        "status": v.status,
                    }
                    for v in latest
                ],
            })
        return APIResponse(
            success=True,
            data={"models": models, "total": len(models)},
            message="MLflow model registry retrieved",
        )
    except Exception as e:
        logger.error(f"MLflow registry error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/players/{player_id}/trajectory", response_model=APIResponse)
async def get_player_trajectory(player_id: str, provider: Optional[str] = None):
    """
    Get the developmental trajectory for a player across consecutive seasons. 
    Also forecasts the likely cluster they will be in for the next 1-2 seasons.
    """
    cache_key = f"{player_id}_{provider}"
    now = time.time()
    
    if cache_key in _trajectory_cache:
        cached_data, timestamp = _trajectory_cache[cache_key]
        if now - timestamp < _TRAJECTORY_CACHE_TTL:
            return cached_data
            
    engine = get_engine()
    
    # In a real impl, we'd fetch actual historical metrics from data-sync/db
    # Mocking longitudinal historical sequence:
    mock_history = [
        {"period": "2023/2024", "metrics": {"minutes_played": 1200, "xg_chain": 0.4}},
        {"period": "2024/2025", "metrics": {"minutes_played": 2400, "xg_chain": 0.8}},
        {"period": "2025/2026", "metrics": {"minutes_played": 3100, "xg_chain": 1.2}}
    ]

    try:
        prediction = engine.predict("player_trajectory_forecaster", {
            "player_id": player_id,
            "history": mock_history
        })
        
        result = APIResponse(
            success=True,
            data=prediction,
            message="Player trajectory computed"
        )
        _trajectory_cache[cache_key] = (result, now)
        return result
    except Exception as e:
        logger.error(f"Error computing trajectory for player {player_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
