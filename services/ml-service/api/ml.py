"""
ML API Endpoints
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
import sys
sys.path.append('/app')
from shared.models.base import APIResponse
from models.predictor import (
    PlayerPerformancePredictor,
    MatchOutcomePredictor,
    PlayerSimilarityFinder
)

router = APIRouter(prefix="/api/v2/ml", tags=["machine-learning"])

# Initialize traditional predictors (compatibility)
player_predictor = PlayerPerformancePredictor()
match_predictor = MatchOutcomePredictor()
similarity_finder = PlayerSimilarityFinder()

# Initialize Clean Architecture Analytics Engine
from engine import AnalyticsEngine
from algorithms.clustering import ClusteringAlgorithm
from algorithms.regression import RegressionAlgorithm

analytics_engine = AnalyticsEngine()
analytics_engine.register_algorithm("clustering", ClusteringAlgorithm())
analytics_engine.register_algorithm("regression", RegressionAlgorithm())

@router.post("/engine/predict/{model_name}", response_model=APIResponse)
async def predict_with_engine(model_name: str, input_data: Dict[str, Any]):
    """Run inference using generic domain AnalyticsEngine."""
    try:
        prediction = analytics_engine.predict(model_name, input_data)
        return APIResponse(
            success=True,
            data={"model": model_name, "prediction": prediction},
            message=f"Prediction successful for {model_name}"
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/engine/train/{model_name}", response_model=APIResponse)
async def train_with_engine(model_name: str, data: List[Dict[str, Any]]):
    """Train a model via the AnalyticsEngine with domain entities."""
    try:
        analytics_engine.train_model(model_name, data)
        return APIResponse(
            success=True,
            data={"model": model_name, "status": "training_completed"},
            message=f"Training complete for {model_name}"
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
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

    return APIResponse(
        success=True,
        data=models,
        message=f"Retrieved {len(models)} models"
    )
