"""
xG (Expected Goals) Model – Logistic Regression trained on Opta shot events.
Trains synchronously at import time using pymongo (no async).
Falls back to a distance-based heuristic when too few goal shots exist.
"""
import logging
import math
import os

logger = logging.getLogger(__name__)

MONGO_URL = os.getenv("MONGODB_URL", "mongodb://root:scoutpro123@mongo:27017/scoutpro?authSource=admin")


class XGModel:
    """Expected-Goals model backed by logistic regression on Opta features."""

    def __init__(self):
        self._model = None
        self._trained = False
        self._train()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _features(x: float, y: float, body_part: str, shot_type: str) -> list:
        dist = math.sqrt((x - 100) ** 2 + (y - 50) ** 2)
        angle = math.degrees(math.atan2(abs(y - 50), max(100 - x, 0.1)))
        is_header = 1 if "head" in str(body_part).lower() else 0
        is_open_play = 1 if str(shot_type).lower() == "open_play" else 0
        return [dist, angle, is_header, is_open_play]

    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------
    def _train(self) -> None:
        try:
            import pymongo
            from sklearn.linear_model import LogisticRegression
            from sklearn.model_selection import train_test_split

            client = pymongo.MongoClient(MONGO_URL, serverSelectionTimeoutMS=5000)
            db = client.get_default_database()
            shots = list(db["match_events"].find(
                {"type_name": "shot"},
                {"location": 1, "is_goal": 1, "raw_event": 1},
            ))
            client.close()

            goal_shots = [s for s in shots if s.get("is_goal")]
            if len(goal_shots) < 5:
                logger.warning(
                    "Only %d goal shots in DB (need ≥5); using heuristic xG fallback.",
                    len(goal_shots),
                )
                return

            X, y = [], []
            for shot in shots:
                loc = shot.get("location") or {}
                raw = shot.get("raw_event") or {}
                feats = self._features(
                    float(loc.get("x", 50)),
                    float(loc.get("y", 50)),
                    str(raw.get("body_part", "")),
                    str(raw.get("shot_type", "")),
                )
                X.append(feats)
                y.append(1 if shot.get("is_goal") else 0)

            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.25, random_state=42
            )
            clf = LogisticRegression(max_iter=500)
            clf.fit(X_train, y_train)
            acc = clf.score(X_test, y_test)
            logger.info(
                "xG model trained on %d shots (goals=%d), test accuracy=%.3f",
                len(shots), len(goal_shots), acc,
            )
            self._model = clf
            self._trained = True

        except Exception as exc:
            logger.error("xG model training failed: %s", exc)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def predict(
        self,
        location_x: float,
        location_y: float,
        body_part: str,
        shot_type: str,
    ) -> float:
        """Return xG in [0, 1]. Falls back to heuristic if model not ready."""
        if self._trained and self._model is not None:
            try:
                feats = self._features(location_x, location_y, body_part, shot_type)
                prob = self._model.predict_proba([feats])[0][1]
                return round(float(prob), 4)
            except Exception as exc:
                logger.error("xG prediction failed: %s", exc)
        # Heuristic fallback: exp(-distance / 30)
        dist = math.sqrt((location_x - 100) ** 2 + (location_y - 50) ** 2)
        return round(math.exp(-dist / 30), 4)

    def is_ready(self) -> bool:
        """Return True if the logistic regression model is trained."""
        return self._trained


# Module-level singleton – created once at import time.
xg_model = XGModel()
