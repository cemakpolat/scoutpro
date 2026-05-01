from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List
import logging
from config.settings import get_settings
from services.feature_pipeline import TimeSeriesFeatureExtractor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2/ml/form", tags=["timeseries", "form"])

# Singleton feature extractor (in a real scenario, this would use Redis for distributed state)
# For the prototype, we initialize it globally.
_time_series_extractor = TimeSeriesFeatureExtractor(window_size=5)

@router.post("/{player_id}/update", response_model=Dict[str, Any])
async def update_player_form(player_id: str, match_stats: Dict[str, float]):
    """
    Ingest aggregated stats from a completed match into the player's rolling window.
    This simulates data flowing from live-ingestion-service or data-sync into the ML store.
    Expected stats: passes, successful_passes, shots, xg
    """
    try:
        _time_series_extractor.update_player_match_stats(player_id, match_stats)
        
        # In a real system, you would also write this array to TimescaleDB or Redis feature store here.
        # This builds our ML-ready feature pipeline.
        
        return {
            "success": True,
            "player_id": player_id,
            "message": "Rolling history updated successfully."
        }
    except Exception as e:
        logger.error(f"Error updating form: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{player_id}", response_model=Dict[str, Any])
async def get_player_form(player_id: str):
    """
    Retrieve the player's current form features (rolling averages, momentum).
    This output tensor is ML-ready and can be directly piped into the Analytics Engine.
    """
    try:
        features = _time_series_extractor.get_player_form_features(player_id)
        
        return {
            "success": True,
            "player_id": player_id,
            "data": features
        }
    except KeyError:
        raise HTTPException(status_code=404, detail="Player form data not initialized. Need match history.")
    except Exception as e:
        logger.error(f"Error retrieving form: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{player_id}/tensor", response_model=Dict[str, Any])
async def get_player_form_tensor(player_id: str):
    """
    Retrieves the raw tensor representation of player form (for internal inference).
    """
    try:
        tensor = _time_series_extractor.get_form_tensor(player_id)
        
        return {
            "success": True,
            "player_id": player_id,
            "tensor": tensor.tolist() if hasattr(tensor, "tolist") else tensor
        }
    except KeyError:
        raise HTTPException(status_code=404, detail="Player form data not initialized.")
    except Exception as e:
        logger.error(f"Error retrieving form tensor: {e}")
        raise HTTPException(status_code=500, detail=str(e))

