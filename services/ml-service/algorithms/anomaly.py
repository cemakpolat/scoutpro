import numpy as np
import logging
from typing import Dict, Any, List

try:
    from sklearn.ensemble import IsolationForest
except ImportError:
    IsolationForest = None

from algorithms.base import MLAlgorithm

logger = logging.getLogger(__name__)

class MatchPerformanceAnomalyDetector(MLAlgorithm):
    """
    Detects irregular match performances (outliers) using Isolation Forest.
    This helps scouts flag when a player drastically overperforms or underperforms
    their rolling form and expected output, pinpointing "breakout" games.
    """

    def __init__(self, contamination: float = 0.1):
        self.contamination = contamination
        self.model = IsolationForest(contamination=self.contamination, random_state=42) if IsolationForest else None
        self.is_fitted = False

    def train(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Fits the anomaly detector on historical match feature arrays.
        Input data should include context like [xG_diff, match_rating, passes_above_average, etc.]
        """
        if not self.model:
            return {"error": "Scikit-Learn IsolationForest not installed."}

        X = []
        for record in data:
            # Flattening composite metrics (difference from rolling form)
            features = [
                float(record.get('xg_differential', 0.0)),
                float(record.get('pass_volume_diff', 0.0)),
                float(record.get('defensive_actions_diff', 0.0)),
                float(record.get('composite_index_deviation', 0.0))
            ]
            X.append(features)

        if len(X) < 10:
            return {"error": "Needs at least 10 historical matches to establish a baseline for anomaly detection."}

        X = np.array(X)
        self.model.fit(X)
        self.is_fitted = True

        return {
            "status": "success",
            "samples": len(X),
            "algorithm": "IsolationForest",
            "contamination": self.contamination
        }

    def predict(self, input_data: Dict[str, Any]) -> Any:
        """
        Predicts if a single match's performance is anomalous.
        Returns the anomaly score and boolean flag.
        """
        if not self.is_fitted or not self.model:
            return {"error": "Anomaly detector is not fitted."}

        try:
            features = [
                float(input_data.get('xg_differential', 0.0)),
                float(input_data.get('pass_volume_diff', 0.0)),
                float(input_data.get('defensive_actions_diff', 0.0)),
                float(input_data.get('composite_index_deviation', 0.0))
            ]
            x_input = np.array(features).reshape(1, -1)

            # predict() returns 1 for inliers, -1 for outliers
            prediction = self.model.predict(x_input)[0]
            # score_samples() returns negative anomaly scores (lower is more abnormal)
            score = self.model.score_samples(x_input)[0]

            is_anomaly = bool(prediction == -1)

            # Provide human readable context
            reasoning = []
            if is_anomaly:
                if features[0] > 1.0: reasoning.append("Vastly exceeded xG expectations.")
                if features[3] > 0.5: reasoning.append("Unusually high absolute composite performance index.")
                if features[3] < -0.5: reasoning.append("Uncharacteristically poor composite alignment output.")

            return {
                "is_outlier": is_anomaly,
                "anomaly_score": float(score),
                "insight": " ".join(reasoning) if reasoning else "Statistical anomaly detected in raw vector distribution.",
            }
        except Exception as e:
            logger.error(f"Anomaly prediction error: {e}")
            return {"error": str(e)}
