"""
Linear Regression Algorithm
Predicts a continuous football metric from player/event statistics.
"""
from typing import Any, List, Dict, Optional
import logging
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, r2_score
from .base import MLAlgorithm

logger = logging.getLogger(__name__)


class LinearRegressionAlgorithm(MLAlgorithm):
    """
    Linear Regression for predicting a continuous target (e.g., goals, xG, pass accuracy).

    Data format (list of dicts from MongoDB player_statistics / player_features):
        [{"player_id": "...", "goals": 5, "shots": 15, "passes": 200, ...}, ...]
    """

    def __init__(self, target_field: str = "goals", test_size: float = 0.2, random_state: int = 42):
        self.target_field = target_field
        self.test_size = test_size
        self.random_state = random_state
        self.model: Optional[LinearRegression] = None
        self.scaler = StandardScaler()
        self.feature_names: List[str] = []
        self.is_fitted = False
        self.metrics: Dict[str, Any] = {}

    def train(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not data:
            return {"error": "No data provided"}

        exclude = {self.target_field, "player_id", "_id", "updated_at", "playerID", "teamID"}
        self.feature_names = [
            k for k in data[0].keys()
            if k not in exclude and isinstance(data[0].get(k), (int, float))
        ]

        X, y = [], []
        for row in data:
            if row.get(self.target_field) is not None:
                feats = [float(row.get(f, 0) or 0) for f in self.feature_names]
                X.append(feats)
                y.append(float(row[self.target_field] or 0))

        if len(X) < 5:
            return {"error": f"Insufficient data ({len(X)} samples with '{self.target_field}')", "n_samples": len(X)}

        X_arr = np.array(X)
        y_arr = np.array(y)

        if len(X) >= 10:
            X_train, X_test, y_train, y_test = train_test_split(
                X_arr, y_arr, test_size=self.test_size, random_state=self.random_state
            )
        else:
            X_train, X_test, y_train, y_test = X_arr, X_arr, y_arr, y_arr

        X_train_s = self.scaler.fit_transform(X_train)
        X_test_s = self.scaler.transform(X_test)

        self.model = LinearRegression()
        self.model.fit(X_train_s, y_train)
        self.is_fitted = True

        y_pred = self.model.predict(X_test_s)
        self.metrics = {
            "n_samples": len(X),
            "n_features": len(self.feature_names),
            "target": self.target_field,
            "features": self.feature_names,
            "r2_score": round(float(r2_score(y_test, y_pred)), 4),
            "mae": round(float(mean_absolute_error(y_test, y_pred)), 4),
        }
        logger.info(f"LinearRegression trained: {self.metrics}")
        return self.metrics

    def predict(self, input_data: Dict[str, Any]) -> Any:
        if not self.is_fitted or self.model is None:
            return {"error": "Model not fitted — call train() first"}
        feats = [float(input_data.get(f, 0) or 0) for f in self.feature_names]
        X = self.scaler.transform(np.array([feats]))
        prediction = float(self.model.predict(X)[0])
        return {
            "predicted_" + self.target_field: round(prediction, 4),
            "model": "linear_regression",
        }
