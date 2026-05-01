from typing import Any, List, Dict, Optional
import logging
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import cross_val_score
from sklearn.preprocessing import StandardScaler
from .base import MLAlgorithm

logger = logging.getLogger(__name__)

class RegressionAlgorithm(MLAlgorithm):
    """
    Gradient Boosting regression for predicting continuous football metrics
    (e.g., expected goals, player performance rating, market value proxy).
    """
    def __init__(self, target_field: str = "goals", n_estimators: int = 100, random_state: int = 42):
        self.target_field = target_field
        self.n_estimators = n_estimators
        self.random_state = random_state
        self.model: Optional[GradientBoostingRegressor] = None
        self.scaler = StandardScaler()
        self.feature_names: List[str] = []
        self.is_fitted = False
        self.cv_scores: List[float] = []

    def train(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Train GBR to predict target_field from other numeric fields.
        data: list of player_statistics or player_features dicts
        """
        if not data:
            return {"error": "No data provided"}

        # Exclude target and ID fields
        exclude = {self.target_field, "player_id", "_id", "updated_at", "playerID", "teamID"}
        self.feature_names = [k for k in data[0].keys() if k not in exclude and isinstance(data[0].get(k), (int, float))]

        X, y = [], []
        for row in data:
            if row.get(self.target_field) is not None:
                feats = [float(row.get(f, 0) or 0) for f in self.feature_names]
                X.append(feats)
                y.append(float(row[self.target_field] or 0))

        if len(X) < 10:
            return {"error": f"Insufficient data with target field '{self.target_field}'", "n_samples": len(X)}

        X_arr = np.array(X)
        X_scaled = self.scaler.fit_transform(X_arr)

        self.model = GradientBoostingRegressor(n_estimators=self.n_estimators, random_state=self.random_state, max_depth=3)

        # Cross-validation
        cv_scores = cross_val_score(self.model, X_scaled, y, cv=min(5, len(X) // 5), scoring="r2")
        self.cv_scores = cv_scores.tolist()
        self.model.fit(X_scaled, y)
        self.is_fitted = True

        return {
            "n_samples": len(X),
            "target": self.target_field,
            "features": self.feature_names,
            "cv_r2_mean": round(float(np.mean(cv_scores)), 4),
            "cv_r2_std": round(float(np.std(cv_scores)), 4),
        }

    def predict(self, input_data: Dict[str, Any]) -> Any:
        """Predict target metric for a player feature dict."""
        if not self.is_fitted or self.model is None:
            return {"error": "Model not fitted"}
        feats = [float(input_data.get(f, 0) or 0) for f in self.feature_names]
        X = np.array([feats])
        X_scaled = self.scaler.transform(X)
        prediction = float(self.model.predict(X_scaled)[0])
        return {"predicted_" + self.target_field: round(prediction, 4)}
