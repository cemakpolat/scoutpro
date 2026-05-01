"""
Logistic Regression Algorithm
Binary or multi-class classification for football events/player data.
"""
from typing import Any, List, Dict, Optional
import logging
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import accuracy_score, classification_report
from .base import MLAlgorithm

logger = logging.getLogger(__name__)


class LogisticRegressionAlgorithm(MLAlgorithm):
    """
    Logistic Regression for classification tasks on player/event data.

    Common use-cases:
    - Goal scored (yes/no) from shot event features
    - Player position classification from performance metrics
    - Match outcome prediction (win/draw/loss)

    Data format (list of dicts from MongoDB):
        [{"player_id": "...", "shots": 3, "xg": 0.45, "position": "Forward", ...}, ...]
    """

    def __init__(
        self,
        target_field: str = "position",
        test_size: float = 0.2,
        random_state: int = 42,
        max_iter: int = 500,
    ):
        self.target_field = target_field
        self.test_size = test_size
        self.random_state = random_state
        self.max_iter = max_iter
        self.model: Optional[LogisticRegression] = None
        self.scaler = StandardScaler()
        self.encoder = LabelEncoder()
        self.feature_names: List[str] = []
        self.classes_: List[str] = []
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

        X, y_raw = [], []
        for row in data:
            label = row.get(self.target_field)
            if label is not None and str(label).strip():
                feats = [float(row.get(f, 0) or 0) for f in self.feature_names]
                X.append(feats)
                y_raw.append(str(label))

        if len(X) < 5:
            return {"error": f"Insufficient data ({len(X)} samples with '{self.target_field}')", "n_samples": len(X)}

        unique_classes = list(set(y_raw))
        if len(unique_classes) < 2:
            return {"error": f"Need at least 2 classes, found: {unique_classes}"}

        X_arr = np.array(X)
        y_arr = self.encoder.fit_transform(y_raw)
        self.classes_ = list(self.encoder.classes_)

        if len(X) >= 10:
            X_train, X_test, y_train, y_test = train_test_split(
                X_arr, y_arr, test_size=self.test_size, random_state=self.random_state, stratify=y_arr if len(unique_classes) <= len(X) // 2 else None
            )
        else:
            X_train, X_test, y_train, y_test = X_arr, X_arr, y_arr, y_arr

        X_train_s = self.scaler.fit_transform(X_train)
        X_test_s = self.scaler.transform(X_test)

        self.model = LogisticRegression(
            solver="lbfgs", max_iter=self.max_iter, random_state=self.random_state, multi_class="auto"
        )
        self.model.fit(X_train_s, y_train)
        self.is_fitted = True

        y_pred = self.model.predict(X_test_s)
        self.metrics = {
            "n_samples": len(X),
            "n_features": len(self.feature_names),
            "target": self.target_field,
            "classes": self.classes_,
            "accuracy": round(float(accuracy_score(y_test, y_pred)), 4),
            "features": self.feature_names,
        }
        logger.info(f"LogisticRegression trained: {self.metrics}")
        return self.metrics

    def predict(self, input_data: Dict[str, Any]) -> Any:
        if not self.is_fitted or self.model is None:
            return {"error": "Model not fitted — call train() first"}
        feats = [float(input_data.get(f, 0) or 0) for f in self.feature_names]
        X = self.scaler.transform(np.array([feats]))
        pred_class_idx = int(self.model.predict(X)[0])
        pred_class = self.classes_[pred_class_idx] if pred_class_idx < len(self.classes_) else str(pred_class_idx)
        probas = self.model.predict_proba(X)[0].tolist()
        return {
            "predicted_" + self.target_field: pred_class,
            "probabilities": {cls: round(p, 4) for cls, p in zip(self.classes_, probas)},
            "model": "logistic_regression",
        }
