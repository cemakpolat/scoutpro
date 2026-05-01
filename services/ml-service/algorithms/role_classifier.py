import numpy as np
import logging
from typing import Dict, Any, List

try:
    from sklearn.cluster import KMeans
except ImportError:
    KMeans = None

from algorithms.base import MLAlgorithm

logger = logging.getLogger(__name__)

class TacticalRoleClassifier(MLAlgorithm):
    """
    Classifies players into distinct tactical roles (e.g., 'Deep-Lying Playmaker', 
    'Box-to-Box', 'Target Man') regardless of their nominal formation position.
    Uses K-Means clustering on aggregated season match data.
    """

    # Hypothetical mapping for a generic 5-cluster system of outfield players.
    ROLE_LABELS = {
        0: "Ball-Winning/Anchor",
        1: "Progressive/Box-to-Box",
        2: "Creative/Playmaker",
        3: "Wide/Winger Attacker",
        4: "Finisher/Target"
    }

    def __init__(self, n_clusters: int = 5):
        self.n_clusters = n_clusters
        self.model = KMeans(n_clusters=self.n_clusters, random_state=42) if KMeans else None
        self.is_fitted = False

    def train(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not self.model:
            return {"error": "Scikit-Learn KMeans not installed."}

        X = []
        for record in data:
            # Flattening composite metrics (Defensive vs Attacking vs Possession)
            features = [
                float(record.get('composite_defending', 0.0)),
                float(record.get('composite_possession', 0.0)),
                float(record.get('composite_attacking', 0.0)),
                float(record.get('pass_accuracy', 0.0)),
                float(record.get('touches_in_box_per_90', 0.0))
            ]
            X.append(features)

        if len(X) < self.n_clusters:
            return {"error": f"Needs at least {self.n_clusters} players to compute tactical roles."}

        X = np.array(X)
        self.model.fit(X)
        self.is_fitted = True

        return {
            "status": "success",
            "samples": len(X),
            "algorithm": "KMeans_TacticalRole",
            "clusters": self.n_clusters
        }

    def predict(self, input_data: Dict[str, Any]) -> Any:
        if not self.is_fitted or not self.model:
            return {"error": "TacticalRoleClassifier is not fitted."}

        try:
            features = [
                float(input_data.get('composite_defending', 0.0)),
                float(input_data.get('composite_possession', 0.0)),
                float(input_data.get('composite_attacking', 0.0)),
                float(input_data.get('pass_accuracy', 0.0)),
                float(input_data.get('touches_in_box_per_90', 0.0))
            ]
            x_input = np.array(features).reshape(1, -1)
            
            cluster_idx = int(self.model.predict(x_input)[0])
            distances = self.model.transform(x_input)[0]
            confidence = 1.0 / (1.0 + float(distances[cluster_idx])) # pseudo-confidence

            return {
                "assigned_role_id": cluster_idx,
                "role_name": self.ROLE_LABELS.get(cluster_idx, f"Role {cluster_idx}"),
                "confidence_score": float(confidence),
                "distance_to_centroid": float(distances[cluster_idx])
            }
        except Exception as e:
            logger.error(f"Role classification error: {e}")
            return {"error": str(e)}
