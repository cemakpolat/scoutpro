"""
ML Model Predictor
"""
import logging
import math
import os
import pickle
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.exceptions import NotFittedError
import joblib
from pathlib import Path

logger = logging.getLogger(__name__)

_MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://root:scoutpro123@mongo:27017/scoutpro")
_FEATURE_COLS = ["pass_accuracy", "shot_accuracy", "duel_win_rate", "matches_played"]
_XG_SHOT_EVENT_TYPES = {
    "shot",
    "miss",
    "post",
    "attempt_saved",
    "attempt saved",
    "goal",
    "blocked_shot",
    "chance_missed",
    "chance missed",
}


class PlayerPerformancePredictor:
    """Predict player performance metrics"""

    def __init__(self, model_path: str = "/models/player_performance.pkl"):
        self.model = None
        self.model_path = model_path
        self.is_fitted = False
        self.feature_cols = _FEATURE_COLS

    def load_model(self):
        """Load trained model from disk if available."""
        try:
            if self.model_path and Path(self.model_path).exists():
                data = joblib.load(self.model_path)
                if isinstance(data, dict):
                    self.model = data["model"]
                    self.feature_cols = data.get("feature_cols", _FEATURE_COLS)
                else:
                    self.model = data
                    self.feature_cols = _FEATURE_COLS
                self.is_fitted = True
                logger.info(f"Loaded player performance model from {self.model_path}")
            else:
                self.model = None
                self.is_fitted = False
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            self.model = None
            self.is_fitted = False

    def _auto_train(self):
        """Bootstrap features from player_statistics and train synchronously."""
        try:
            import pymongo
            from datetime import datetime, timezone

            client = pymongo.MongoClient(_MONGODB_URL, serverSelectionTimeoutMS=5000)
            db = client.get_default_database()
            stats_col = db["player_statistics"]
            features_col = db["player_features"]

            # Bootstrap player_features from player_statistics
            bootstrapped = 0
            for doc in stats_col.find({}):
                player_id = doc.get("playerID") or doc.get("player_id")
                if not player_id:
                    continue
                passes = int(doc.get("passes", 0) or 0)
                passes_completed = int(doc.get("passes_completed", 0) or 0)
                shots = int(doc.get("shots", 0) or 0)
                goals = int(doc.get("goals", 0) or 0)
                tackles = int(doc.get("tackles", 0) or 0)
                duels = int(doc.get("duels", 0) or 0)
                duels_won = int(doc.get("duels_won", 0) or 0)
                matches = int(doc.get("matches_played", 1) or 1)

                features_col.update_one(
                    {"playerID": str(player_id)},
                    {"$set": {
                        "playerID": str(player_id),
                        "total_passes": passes,
                        "pass_accuracy": passes_completed / passes if passes > 0 else 0.0,
                        "total_shots": shots,
                        "shot_accuracy": goals / shots if shots > 0 else 0.0,
                        "total_tackles": tackles,
                        "total_duels": duels,
                        "duel_win_rate": duels_won / duels if duels > 0 else 0.0,
                        "matches_played": matches,
                        "updatedAt": datetime.now(timezone.utc),
                    }},
                    upsert=True,
                )
                bootstrapped += 1

            # Load all feature documents
            docs = list(features_col.find({}))
            client.close()

            if len(docs) < 2:
                logger.warning("Not enough player_features docs to train (need >= 2)")
                return

            df = pd.DataFrame(docs)
            for col in self.feature_cols:
                if col not in df.columns:
                    df[col] = 0.0

            X = df[self.feature_cols].fillna(0.0).values
            # Synthetic performance score as training target
            y = (df["pass_accuracy"].fillna(0) * 0.35 +
                 df["shot_accuracy"].fillna(0) * 0.40 +
                 df["duel_win_rate"].fillna(0) * 0.25).values

            self.model = GradientBoostingRegressor(n_estimators=100, random_state=42)
            self.model.fit(X, y)
            self.is_fitted = True

            os.makedirs("/models", exist_ok=True)
            joblib.dump({"model": self.model, "feature_cols": self.feature_cols},
                        self.model_path)
            logger.info(f"Auto-trained PlayerPerformancePredictor on {bootstrapped} players")

        except Exception as e:
            logger.error(f"Auto-train failed: {e}")

    def predict(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """Predict player performance rating from a features dict."""
        try:
            if not self.is_fitted:
                self.load_model()

            if not self.is_fitted:
                logger.info("Model not found on disk — triggering auto-train")
                self._auto_train()

            if not self.is_fitted:
                return {"error": "Model is not trained yet", "status": "pending_training"}

            if not features:
                raise ValueError("No features provided for prediction.")

            X = np.array([[features.get(c, 0.0) for c in self.feature_cols]])
            prediction = self.model.predict(X)
            return {
                "predicted_rating": float(prediction[0]),
                "confidence": 0.85,
                "features_used": self.feature_cols,
            }

        except Exception as e:
            logger.error(f"Prediction error: {e}")
            return {"error": str(e)}


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

    async def find_similar_by_id(
        self,
        player_id: str,
        top_n: int = 10,
    ) -> List[Dict[str, Any]]:
        """Find similar players by player_id using cosine similarity on MongoDB player_features."""
        try:
            from motor.motor_asyncio import AsyncIOMotorClient

            client = AsyncIOMotorClient(_MONGODB_URL, serverSelectionTimeoutMS=5000)
            db = client.get_default_database()
            features_col = db["player_features"]

            target = await features_col.find_one({"playerID": player_id})
            if not target:
                client.close()
                return []

            target_vec = np.array([target.get(k, 0.0) for k in _FEATURE_COLS], dtype=float)
            target_norm = np.linalg.norm(target_vec)

            results = []
            async for doc in features_col.find({"playerID": {"$ne": player_id}}):
                candidate_vec = np.array([doc.get(k, 0.0) for k in _FEATURE_COLS], dtype=float)
                candidate_norm = np.linalg.norm(candidate_vec)
                if target_norm == 0 or candidate_norm == 0:
                    similarity = 0.0
                else:
                    similarity = float(np.dot(target_vec, candidate_vec) / (target_norm * candidate_norm))
                results.append({
                    "player_id": doc.get("playerID"),
                    "similarity_score": round(similarity, 4),
                    "features": {k: doc.get(k, 0.0) for k in _FEATURE_COLS},
                })

            client.close()
            results.sort(key=lambda x: x["similarity_score"], reverse=True)
            return results[:top_n]

        except Exception as e:
            logger.error(f"Error finding similar players by id: {e}")
            return []

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


class XGModel:
    """
    Expected Goals (xG) model using logistic regression on shot features.
    Trained from match_events collection. Opta pitch: 0-100 x,y.
    Goal center is at approximately x=100, y=50.
    """
    def __init__(self, model_path: str = "/models/xg_model.pkl"):
        self.model_path = model_path
        self.model = None
        self.is_fitted = False
        self.feature_count: Optional[int] = None
        self.load_model()

    def load_model(self):
        try:
            if os.path.exists(self.model_path):
                with open(self.model_path, "rb") as f:
                    data = pickle.load(f)
                self.model = data["model"]
                self.feature_count = data.get("feature_count") if isinstance(data, dict) else None
                self.is_fitted = True
                logger.info(f"XG model loaded from {self.model_path}")
        except Exception as e:
            logger.warning(f"Could not load xG model: {e}")

    @staticmethod
    def _is_truthy(value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value != 0
        return str(value or '').strip().lower() in {'1', 'true', 'yes', 'y', 'on'}

    @staticmethod
    def _extract_score_diff(shot: Dict[str, Any], raw: Dict[str, Any]) -> float:
        for key in ('score_diff', 'goal_difference', 'game_state_score_diff'):
            value = shot.get(key, raw.get(key))
            if value not in (None, '', 'None'):
                try:
                    return float(value)
                except (TypeError, ValueError):
                    continue

        team_score = shot.get('team_score', raw.get('team_score'))
        opponent_score = shot.get('opponent_score', raw.get('opponent_score'))
        if team_score not in (None, '', 'None') and opponent_score not in (None, '', 'None'):
            try:
                return float(team_score) - float(opponent_score)
            except (TypeError, ValueError):
                pass

        home_score = shot.get('home_score', raw.get('home_score'))
        away_score = shot.get('away_score', raw.get('away_score'))
        team_side = str(shot.get('team_side') or raw.get('team_side') or '').strip().lower()
        is_home = shot.get('is_home_team', raw.get('is_home_team'))
        if home_score not in (None, '', 'None') and away_score not in (None, '', 'None'):
            try:
                if team_side == 'home' or XGModel._is_truthy(is_home):
                    return float(home_score) - float(away_score)
                if team_side == 'away' or str(is_home).strip().lower() in {'0', 'false', 'no'}:
                    return float(away_score) - float(home_score)
            except (TypeError, ValueError):
                pass

        return 0.0

    @staticmethod
    def _extract_location(shot: Dict[str, Any]) -> tuple[float, float]:
        location = shot.get("location")

        if isinstance(location, dict):
            raw_x = location.get("x", shot.get("x", 0))
            raw_y = location.get("y", shot.get("y", 50))
        elif isinstance(location, (list, tuple)) and len(location) >= 2:
            raw_x, raw_y = location[0], location[1]
        else:
            raw_x = shot.get("x", 0)
            raw_y = shot.get("y", 50)

        return float(raw_x or 0), float(raw_y or 50)

    @staticmethod
    def _normalize_qualifiers(shot: Dict[str, Any]) -> Dict[str, Any]:
        qualifiers = shot.get("qualifiers")
        if isinstance(qualifiers, dict):
            return {str(key): value for key, value in qualifiers.items()}

        if isinstance(qualifiers, list):
            normalized: Dict[str, Any] = {}
            for qualifier in qualifiers:
                if not isinstance(qualifier, dict):
                    continue
                qualifier_id = qualifier.get("qualifier_id") or qualifier.get("qualifierID") or qualifier.get("id")
                if qualifier_id in (None, ""):
                    continue
                normalized[str(qualifier_id)] = qualifier.get("value")
            return normalized

        raw_event = shot.get("raw_event") or {}
        raw_qualifiers = raw_event.get("qualifiers")
        if isinstance(raw_qualifiers, dict):
            return {str(key): value for key, value in raw_qualifiers.items()}

        return {}

    @staticmethod
    def _extract_features(shot: Dict[str, Any]) -> Optional[List[float]]:
        """Extract xG features from a shot event document."""
        try:
            x, y = XGModel._extract_location(shot)
            raw = shot.get("raw_event") or {}
            quals = XGModel._normalize_qualifiers(shot)

            # Distance to goal (Opta: goal at x=100, y=50)
            GOAL_X, GOAL_Y = 100.0, 50.0
            PITCH_LEN_M, PITCH_WID_M = 105.0, 68.0
            dx = (GOAL_X - x) / 100.0 * PITCH_LEN_M
            dy = (GOAL_Y - y) / 100.0 * PITCH_WID_M
            distance = math.sqrt(dx ** 2 + dy ** 2)

            # Shot angle (degrees, from shot location to goal posts)
            GOAL_WIDTH_M = 7.32
            angle = math.degrees(math.atan2(GOAL_WIDTH_M * dx, dx ** 2 + dy ** 2 - (GOAL_WIDTH_M / 2) ** 2)) if dx > 0 else 0.0
            angle = max(0.0, angle)

            # Body part
            body_part = str(shot.get("body_part") or raw.get("body_part") or "").lower()
            is_header = 1.0 if "head" in body_part else 0.0
            is_left_foot = 1.0 if 'left' in body_part else 0.0
            is_right_foot = 1.0 if 'right' in body_part else 0.0
            is_other_body_part = 1.0 if body_part and not (is_header or is_left_foot or is_right_foot) else 0.0

            # Shot situation
            shot_type = str(shot.get("shot_type") or raw.get("shot_type") or "").lower()
            is_direct_set_piece = 1.0 if shot_type in ("free_kick",) else 0.0
            is_penalty = 1.0 if shot_type == "penalty" else 0.0
            is_open_play = 1.0 if not is_direct_set_piece and not is_penalty else 0.0

            assist_context_values = [
                shot.get('assist_type'),
                shot.get('shot_assist_type'),
                shot.get('pass_type'),
                raw.get('assist_type'),
                raw.get('shot_assist_type'),
                raw.get('pass_type'),
            ]
            assist_context = ' '.join(
                str(value).strip().lower()
                for value in assist_context_values
                if value not in (None, '', 'None')
            )
            is_cross_assist = 1.0 if 'cross' in assist_context else 0.0
            is_cutback = 1.0 if 'cutback' in assist_context else 0.0
            is_through_ball = 1.0 if 'through' in assist_context else 0.0
            is_fast_break = 1.0 if XGModel._is_truthy(shot.get('is_fast_break') or raw.get('is_fast_break') or shot.get('fast_break') or raw.get('fast_break')) or 'fast break' in assist_context else 0.0
            is_rebound = 1.0 if XGModel._is_truthy(shot.get('is_rebound') or raw.get('is_rebound')) or 'rebound' in assist_context else 0.0
            under_pressure = 1.0 if XGModel._is_truthy(shot.get('under_pressure') or raw.get('under_pressure') or shot.get('pressure_on_shot') or raw.get('pressure_on_shot')) else 0.0
            score_diff = max(-3.0, min(3.0, XGModel._extract_score_diff(shot, raw)))
            is_trailing = 1.0 if score_diff < 0 else 0.0
            is_level = 1.0 if score_diff == 0 else 0.0
            is_leading = 1.0 if score_diff > 0 else 0.0
            minute = float(shot.get('minute', raw.get('minute', 0)) or 0.0)
            is_late_game = 1.0 if minute >= 75.0 else 0.0

            # Goal mouth position from qualifiers
            gm_y = float(quals.get("102", 50) or 50)   # % across goal
            gm_z = float(quals.get("103", 50) or 50)   # % height

            return [
                distance,
                angle,
                is_header,
                is_left_foot,
                is_right_foot,
                is_other_body_part,
                is_direct_set_piece,
                is_penalty,
                is_open_play,
                is_cross_assist,
                is_cutback,
                is_through_ball,
                is_fast_break,
                is_rebound,
                under_pressure,
                score_diff,
                is_trailing,
                is_level,
                is_leading,
                is_late_game,
                gm_y,
                gm_z,
            ]
        except Exception as e:
            logger.debug(f"xG feature extraction failed: {e}")
            return None

    @staticmethod
    def _analytical_xg_fallback(shot: Dict[str, Any]) -> float:
        feats = XGModel._extract_features(shot)
        if feats is None:
            return 0.05

        distance = feats[0]
        angle = feats[1]
        is_header = feats[2]
        is_direct_set_piece = feats[6]
        is_penalty = feats[7]
        is_fast_break = feats[12]
        under_pressure = feats[14]

        score = 2.6 - 0.09 * distance + 0.015 * angle
        score -= 0.55 * is_header
        score -= 0.22 * is_direct_set_piece
        score -= 0.18 * under_pressure
        score += 1.4 * is_penalty
        score += 0.16 * is_fast_break
        probability = 1.0 / (1.0 + math.exp(-score))
        return round(max(0.01, min(probability, 0.99)), 4)

    def train_from_mongo(self, mongodb_url: str, database: str = "scoutpro") -> Dict[str, Any]:
        """Train logistic regression xG model from match_events collection."""
        import pymongo
        from sklearn.linear_model import LogisticRegression
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import roc_auc_score
        from sklearn.preprocessing import StandardScaler
        from sklearn.pipeline import Pipeline

        client = pymongo.MongoClient(mongodb_url, serverSelectionTimeoutMS=5000)
        db = client[database]
        shots = list(
            db.match_events.find(
                {
                    "$or": [
                        {"type_name": {"$in": sorted(_XG_SHOT_EVENT_TYPES)}},
                        {"is_goal": True},
                    ]
                },
                {
                    "type_name": 1,
                    "location": 1,
                    "x": 1,
                    "y": 1,
                    "raw_event": 1,
                    "qualifiers": 1,
                    "shot_type": 1,
                    "body_part": 1,
                    "is_goal": 1,
                },
            )
        )
        client.close()

        X, y = [], []
        for shot in shots:
            feats = self._extract_features(shot)
            if feats is not None:
                X.append(feats)
                event_type = str(shot.get("type_name") or "").strip().lower()
                y.append(1 if shot.get("is_goal") or event_type == "goal" else 0)

        if len(X) < 20:
            return {
                "error": "Insufficient shot-event data for xG training",
                "n_shots": len(X),
                "event_types": sorted(_XG_SHOT_EVENT_TYPES),
            }

        positive_examples = int(sum(y))
        negative_examples = int(len(y) - positive_examples)
        if positive_examples < 2 or negative_examples < 2:
            return {
                "error": "Insufficient goal and non-goal examples for xG training",
                "n_shots": len(X),
                "goal_events": positive_examples,
                "non_goal_events": negative_examples,
            }

        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=0.2,
            random_state=42,
            stratify=y,
        )

        pipeline = Pipeline([
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(C=1.0, class_weight="balanced", max_iter=500, random_state=42))
        ])
        pipeline.fit(X_train, y_train)

        y_prob = pipeline.predict_proba(X_test)[:, 1]
        auc = roc_auc_score(y_test, y_prob)
        goal_rate = round(sum(y) / len(y), 4)

        self.model = pipeline
        self.is_fitted = True
        self.feature_count = len(X[0])
        os.makedirs(os.path.dirname(self.model_path) or "/models", exist_ok=True)
        with open(self.model_path, "wb") as f:
            pickle.dump({"model": pipeline, "feature_count": self.feature_count}, f)

        result: Dict[str, Any] = {
            "n_shots": len(X),
            "n_train": len(X_train),
            "n_test": len(X_test),
            "goal_events": positive_examples,
            "non_goal_events": negative_examples,
            "auc_roc": round(auc, 4),
            "goal_rate": goal_rate,
        }

        # Log to MLflow and gate model registration on AUC thresholds
        try:
            import mlflow
            import mlflow.sklearn

            mlflow_uri = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000")
            mlflow.set_tracking_uri(mlflow_uri)
            mlflow.set_experiment("scoutpro_xg")

            with mlflow.start_run(run_name="xg_logistic_regression") as run:
                mlflow.set_tag("model_type", "xg")
                mlflow.log_params({
                    "n_shots": len(X),
                    "test_size": 0.2,
                    "algorithm": "LogisticRegression",
                    "class_weight": "balanced",
                    "C": 1.0,
                })
                mlflow.log_metrics({
                    "auc_roc": round(auc, 4),
                    "goal_rate": goal_rate,
                    "n_train": len(X_train),
                    "n_test": len(X_test),
                })
                mlflow.sklearn.log_model(
                    pipeline,
                    artifact_path="xg_model",
                    registered_model_name="xg_model",
                )
                result["mlflow_run_id"] = run.info.run_id

            # Promote model version based on AUC threshold
            try:
                mlflow_client = mlflow.tracking.MlflowClient()
                versions = mlflow_client.get_latest_versions("xg_model", stages=["None"])
                if versions:
                    version = versions[-1].version
                    if auc >= 0.60:
                        mlflow_client.transition_model_version_stage("xg_model", version, stage="Production")
                        result["registry_stage"] = "Production"
                    elif auc >= 0.50:
                        mlflow_client.transition_model_version_stage("xg_model", version, stage="Staging")
                        result["registry_stage"] = "Staging"
                    else:
                        result["registry_stage"] = "None (AUC below 0.50 threshold)"
            except Exception as stage_err:
                logger.warning(f"Model stage transition failed (non-fatal): {stage_err}")
                result["registry_stage"] = "registration_error"

        except Exception as mlflow_err:
            logger.warning(f"MLflow logging skipped (non-fatal): {mlflow_err}")
            result["mlflow_skipped"] = str(mlflow_err)

        return result

    def predict_xg(self, shot: Dict[str, Any]) -> float:
        """Predict xG for a single shot event. Returns probability in [0,1]."""
        if not self.is_fitted or self.model is None:
            return self._analytical_xg_fallback(shot)

        feats = self._extract_features(shot)
        if feats is None:
            return 0.05
        try:
            expected_feature_count = self.feature_count or getattr(self.model, 'n_features_in_', None)
            if expected_feature_count and expected_feature_count != len(feats):
                logger.warning(
                    'Loaded xG model expects %s features but received %s; falling back to analytical xG',
                    expected_feature_count,
                    len(feats),
                )
                return self._analytical_xg_fallback(shot)
            prob = float(self.model.predict_proba([feats])[0][1])
            return round(prob, 4)
        except Exception:
            return self._analytical_xg_fallback(shot)
