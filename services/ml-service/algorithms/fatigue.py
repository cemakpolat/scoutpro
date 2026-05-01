import numpy as np
import logging
from typing import Dict, Any, List
from algorithms.base import MLAlgorithm

try:
    from sklearn.linear_model import LogisticRegression
except ImportError:
    LogisticRegression = None

logger = logging.getLogger(__name__)

class PhysicalFatiguePredictor(MLAlgorithm):
    """
    Predicts the likelihood of a player experiencing drastic performance drop-off 
    or muscle fatigue (Risk Score) based on consecutive minutes played and match density.
    """
    def __init__(self, risk_threshold: float = 0.65):
        self.risk_threshold = risk_threshold
        self.model = LogisticRegression(class_weight='balanced') if LogisticRegression else None
        self.is_fitted = False

    def train(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        X features: [minutes_played_last_14_days, days_since_last_match, average_distance_covered, age]
        Y target: (binary) Did they underperform base xG or get subbed early? 1=yes, 0=no.
        """
        if not self.model:
            return {"error": "Scikit-Learn LogisticRegression not installed."}

        X, y = [], []
        for record in data:
            # Hypothetical training format
            if 'fatigued_event' in record:
                features = [
                    float(record.get('minutes_last_14d', 0)),
                    float(record.get('days_since_last', 7.0)),
                    float(record.get('age', 25.0)),
                    float(record.get('intensity_index', 1.0)) # sprints/distance
                ]
                X.append(features)
                y.append(int(record['fatigued_event']))

        if len(X) < 10:
            return {"error": "Insufficient data to train fatigue predictor."}

        X = np.array(X)
        y = np.array(y)
        self.model.fit(X, y)
        self.is_fitted = True

        return {"status": "success", "samples": len(X), "algorithm": "LogisticRegression_Fatigue"}

    def predict(self, input_data: Dict[str, Any]) -> Any:
        """
        Calculates the fatigue risk percentage for an upcoming match.
        """
        if not self.is_fitted or not self.model:
            return {"error": "FatiguePredictor is not fitted."}

        try:
            features = [
                float(input_data.get('minutes_last_14d', 0)),
                float(input_data.get('days_since_last', 7.0)),
                float(input_data.get('age', 25.0)),
                float(input_data.get('intensity_index', 1.0))
            ]
            x_input = np.array(features).reshape(1, -1)
            
            # Predict probabilities
            probs = self.model.predict_proba(x_input)[0]
            fatigue_risk = float(probs[1]) # probability of class 1 (fatigued)
            
            recommendation = "Optimal"
            if fatigue_risk > self.risk_threshold:
                recommendation = "High Risk - Consider minor rotation."
            elif fatigue_risk > 0.4:
                recommendation = "Caution - Monitoring required."

            return {
                "fatigue_risk_percentage": fatigue_risk * 100.0,
                "is_high_risk": bool(fatigue_risk > self.risk_threshold),
                "recommendation": recommendation,
                "contributing_factor": "minutes_last_14d" if features[0] > 360 else ("days_since_last" if features[1] < 3 else "age/intensity")
            }
        except Exception as e:
            logger.error(f"Fatigue prediction error: {e}")
            return {"error": str(e)}
