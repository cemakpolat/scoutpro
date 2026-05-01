from typing import Dict, Any, List, Optional
import numpy as np
from algorithms.base import MLAlgorithm
import logging

try:
    from sklearn.linear_model import Ridge
except ImportError:
    Ridge = None

logger = logging.getLogger(__name__)

class TimeSeriesForecaster(MLAlgorithm):
    """
    Time-series forecasting algorithm for next-match predictions.
    Utilizes rolling averages and momentum tensors from the feature pipeline.
    """

    def __init__(self, target_field: str = "next_xg", window_size: int = 5):
        self.target_field = target_field
        self.window_size = window_size
        self.model = Ridge(alpha=1.0) if Ridge else None
        self.is_fitted = False
        
    def extract_features(self, record: dict) -> np.ndarray:
        """
        Expects a record containing rolling statistics and momentum context.
        Returns a numpy array of features.
        """
        # The ML-ready features from TimeSeriesFeatureExtractor
        return np.array([
            record.get("rolling_passes", 0.0),
            record.get("rolling_pass_accuracy", 0.0),
            record.get("rolling_shots", 0.0),
            record.get("rolling_xg", 0.0),
            record.get("momentum_xg", 0.0)
        ], dtype=np.float32)

    def train(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Trains the forecaster. The data must contain both the rolling features 
        and the ground truth for the next match (target_field).
        """
        if not self.model:
            return {"error": "Scikit-Learn not installed."}

        X, y = [], []
        for record in data:
            if self.target_field in record:
                X.append(self.extract_features(record))
                # For form analysis, target is usually next match's performance
                y.append(float(record[self.target_field]))

        if len(X) < 2:
            return {"error": f"Insufficient time-series data for target '{self.target_field}'."}

        X = np.array(X)
        y = np.array(y)

        self.model.fit(X, y)
        self.is_fitted = True
        
        # Calculate a simple baseline R^2 score
        score = self.model.score(X, y)

        return {
            "status": "success",
            "samples": len(X),
            "window_size": self.window_size,
            "target": self.target_field,
            "r_squared": float(score)
        }

    def predict(self, input_data: Dict[str, Any]) -> Any:
        """
        Forecast the designated metric for the next match.
        Input should be the player's current form tensor (as a dict).
        """
        if not self.is_fitted or not self.model:
            return {"error": "Model completely unfitted or unavailable."}

        try:
            x_input = self.extract_features(input_data).reshape(1, -1)
            prediction = self.model.predict(x_input)[0]
            
            return {
                "forecast": max(0.0, float(prediction)), # non-negative
                "target": self.target_field,
                "momentum_impact": input_data.get("momentum_xg", 0.0) * float(self.model.coef_[-1]) if len(self.model.coef_) > 4 else 0.0
            }
        except Exception as e:
            logger.error(f"Time-series prediction error: {e}")
            return {"error": str(e)}

