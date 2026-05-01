import numpy as np
import logging
from typing import Dict, Any, List
from algorithms.base import MLAlgorithm

try:
    from sklearn.ensemble import RandomForestRegressor
except ImportError:
    RandomForestRegressor = None

logger = logging.getLogger(__name__)

class ExpectedGoalsOnTargetModel(MLAlgorithm):
    """
    Predicts xGOT (Expected Goals on Target), providing context on finishing quality.
    Builds on top of raw xG by analyzing trajectory, defensive block, and strike quality.
    """
    def __init__(self, n_estimators: int = 100):
        self.n_estimators = n_estimators
        self.model = RandomForestRegressor(n_estimators=self.n_estimators, random_state=42) if RandomForestRegressor else None
        self.is_fitted = False

    def train(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        X features: [xg_value, shot_distance, angle_to_goal, speed, pressure_index]
        Y target: 1 (goal) or 0 (saved/miss). In real systems, xGOT is trained on post-shot probability.
        """
        if not self.model:
            return {"error": "Scikit-Learn RandomForestRegressor not installed."}

        X, y = [], []
        for record in data:
            if 'is_goal' in record:
                features = [
                    float(record.get('xg_value', 0.1)),
                    float(record.get('shot_distance', 18.0)),
                    float(record.get('angle_to_goal', 30.0)),
                    float(record.get('pressure_index', 0.5))
                ]
                X.append(features)
                y.append(float(record['is_goal']))

        if len(X) < 10:
            return {"error": "Insufficient data to train xGOT model."}

        X = np.array(X)
        y = np.array(y)
        self.model.fit(X, y)
        self.is_fitted = True

        return {"status": "success", "samples": len(X), "algorithm": "RandomForest_xGOT"}

    def predict(self, input_data: Dict[str, Any]) -> Any:
        if not self.is_fitted or not self.model:
            return {"error": "xGOT model is not fitted."}

        try:
            features = [
                float(input_data.get('xg_value', 0.1)),
                float(input_data.get('shot_distance', 18.0)),
                float(input_data.get('angle_to_goal', 30.0)),
                float(input_data.get('pressure_index', 0.5))
            ]
            x_input = np.array(features).reshape(1, -1)
            
            xgot_val = float(self.model.predict(x_input)[0])
            
            # Post-shot value should ideally be bounded between 0 and 1
            xgot_val = max(0.0, min(1.0, xgot_val))

            return {
                "xgot_value": xgot_val,
                "added_value": xgot_val - float(input_data.get('xg_value', 0.1)),
                "finishing_quality": "Elite" if (xgot_val - float(input_data.get('xg_value', 0.1))) > 0.15 else ("Poor" if (xgot_val - float(input_data.get('xg_value', 0.1))) < -0.15 else "Average")
            }
        except Exception as e:
            logger.error(f"xGOT prediction error: {e}")
            return {"error": str(e)}
