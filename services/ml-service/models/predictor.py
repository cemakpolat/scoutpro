"""
ML Model Predictor
"""
import logging
from typing import Dict, Any, List
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.exceptions import NotFittedError
import joblib
from pathlib import Path

logger = logging.getLogger(__name__)


class PlayerPerformancePredictor:
    """Predict player performance metrics"""

    def __init__(self, model_path: str = None):
        self.model = None
        self.model_path = model_path
        self.is_fitted = False

    def load_model(self):
        """Load trained model"""
        try:
            if self.model_path and Path(self.model_path).exists():
                self.model = joblib.load(self.model_path)
                self.is_fitted = True
                logger.info(f"Loaded model from {self.model_path}")
            else:
                # Initialize empty model
                self.model = GradientBoostingRegressor(n_estimators=100)
                self.is_fitted = False
                logger.info("Using uninitialized default model")
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            self.model = GradientBoostingRegressor(n_estimators=100)
            self.is_fitted = False

    def predict(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """Predict player performance"""
        try:
            if not self.model:
                self.load_model()

            if not features:
                raise ValueError("No features provided for prediction.")

            # Convert features to DataFrame
            df = pd.DataFrame([features])

            # Make prediction
            try:
                prediction = self.model.predict(df)
                return {
                    "predicted_rating": float(prediction[0]),
                    "confidence": 0.85, 
                    "features_used": list(features.keys())
                }
            except NotFittedError:
                logger.warning("PlayerPerformancePredictor model is not fitted.")
                return {
                    "error": "Model is not trained yet",
                    "status": "pending_training"
                }

        except Exception as e:
            logger.error(f"Prediction error: {e}")
            return {
                "error": str(e)
            }


class MatchOutcomePredictor:
    """Predict match outcomes"""

    def __init__(self, model_path: str = None):
        self.model = None
        self.model_path = model_path
        self.is_fitted = False

    def load_model(self):
        """Load trained model"""
        try:
            if self.model_path and Path(self.model_path).exists():
                self.model = joblib.load(self.model_path)
                self.is_fitted = True
            else:
                self.model = RandomForestClassifier(n_estimators=100)
                self.is_fitted = False
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            self.model = RandomForestClassifier(n_estimators=100)
            self.is_fitted = False

    def predict(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """Predict match outcome"""
        try:
            if not self.model:
                self.load_model()
                
            if not features:
                raise ValueError("No features provided for prediction.")
                
            df = pd.DataFrame([features])
            
            try:
                probabilities = self.model.predict_proba(df)[0]
                classes = self.model.classes_
                
                # Assuming classes are [away_win, draw, home_win] or similar
                # This depends on how it is trained, we will return dynamic mapping
                prob_map = {str(c): float(p) for c, p in zip(classes, probabilities)}
                
                prediction = self.model.predict(df)[0]
                
                return {
                    "probabilities": prob_map,
                    "predicted_outcome": str(prediction)
                }
            except NotFittedError:
                logger.warning("MatchOutcomePredictor model is not fitted.")
                return {
                    "error": "Model is not trained yet",
                    "status": "pending_training"
                }

        except Exception as e:
            logger.error(f"Prediction error: {e}")
            return {
                "error": str(e)
            }


class PlayerSimilarityFinder:
    """Find similar players"""

    def find_similar_players(
        self,
        player_stats: Dict[str, Any],
        candidate_players: List[Dict[str, Any]],
        top_n: int = 10
    ) -> List[Dict[str, Any]]:
        """Find most similar players based on statistics"""
        try:
            if not player_stats or not candidate_players:
                return []
                
            similarities = []

            for candidate in candidate_players:
                similarity = self._calculate_similarity(player_stats, candidate)
                similarities.append({
                    "player_id": candidate.get("player_id"),
                    "similarity_score": similarity,
                    "stats": candidate
                })

            # Sort by similarity
            similarities.sort(key=lambda x: x["similarity_score"], reverse=True)

            return similarities[:top_n]
        except Exception as e:
            logger.error(f"Error finding similar players: {e}")
            return []

    def _calculate_similarity(self, stats1: Dict[str, Any], stats2: Dict[str, Any]) -> float:
        """Calculate similarity score between two player stat dictionaries"""
        common_keys = set(stats1.keys()) & set(stats2.keys())

        if not common_keys:
            return 0.0

        # Calculate cosine similarity on common numeric fields
        vec1 = [stats1.get(k, 0) for k in common_keys if isinstance(stats1.get(k), (int, float))]
        vec2 = [stats2.get(k, 0) for k in common_keys if isinstance(stats2.get(k), (int, float))]

        if not vec1 or not vec2:
            return 0.0

        # Cosine similarity
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(dot_product / (norm1 * norm2))
