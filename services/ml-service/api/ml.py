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
}

def _is_not_fitted_error(prediction: Dict[str, Any]) -> bool:
    msg = str(prediction.get("error", "")).lower()
    return any(phrase in msg for phrase in _NOT_FITTED_PHRASES)

@router.post("/engine/predict/{algorithm_name}", response_model=APIResponse)
async def predict_with_engine(algorithm_name: str, input_data: Dict[str, Any]):
    """Run inference using the AnalyticsEngine. Body: arbitrary feature dict."""
    try:
        engine = get_engine()
        prediction = engine.predict(algorithm_name, input_data)

        if isinstance(prediction, dict) and "error" in prediction:
            error_msg = str(prediction["error"])

            if _is_not_fitted_error(prediction):
                # Attempt auto-train from MongoDB before giving up
                settings = _get_settings()
                collection = _ALGORITHM_COLLECTION_MAP.get(algorithm_name, "player_statistics")
                try:
                    train_result = engine.train_from_mongo(
                        algorithm_name, settings.mongodb_url, collection=collection
                    )
                    if "error" not in train_result:
                        prediction = engine.predict(algorithm_name, input_data)
                        if isinstance(prediction, dict) and "error" not in prediction:
                            return APIResponse(
                                success=True,
                                data={"algorithm": algorithm_name, "prediction": prediction},
                                message=f"Prediction successful for {algorithm_name}",
                            )
                except Exception as train_err:
                    logger.warning(f"Auto-train failed for {algorithm_name}: {train_err}")

                # Return graceful 200 — model not yet trainable (not enough data)
                return APIResponse(
                    success=False,
                    data={"algorithm": algorithm_name, "available": False, "reason": error_msg},
                    message=f"{algorithm_name} requires additional training data.",
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
