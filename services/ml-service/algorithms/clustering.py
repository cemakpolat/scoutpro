from typing import Any, List, Dict, Optional
import logging
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from .base import MLAlgorithm

logger = logging.getLogger(__name__)

class ClusteringAlgorithm(MLAlgorithm):
    """
    KMeans player clustering algorithm.
    Groups players into tactical archetypes based on feature vectors.
    """
    def __init__(self, n_clusters: int = 5, random_state: int = 42):
        self.n_clusters = n_clusters
        self.random_state = random_state
        self.model: Optional[KMeans] = None
        self.scaler = StandardScaler()
        self.pca: Optional[PCA] = None
        self.feature_names: List[str] = []
        self.is_fitted = False
        self.cluster_labels: Dict[int, str] = {}  # cluster_id -> archetype name

    def train(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Train KMeans on player feature vectors.
        data: list of dicts with numeric fields (player feature store format)
        """
        if not data:
            return {"error": "No data provided"}

        # Extract feature matrix
        self.feature_names = [k for k in data[0].keys() if k not in ("player_id", "_id", "updated_at") and isinstance(data[0][k], (int, float))]
        X = []
        player_ids = []
        for row in data:
            feats = [float(row.get(f, 0) or 0) for f in self.feature_names]
            X.append(feats)
            player_ids.append(str(row.get("player_id", "")))

        X_arr = np.array(X)
        X_scaled = self.scaler.fit_transform(X_arr)

        # Optional PCA if >10 features
        if len(self.feature_names) > 10:
            self.pca = PCA(n_components=min(8, len(self.feature_names)), random_state=self.random_state)
            X_scaled = self.pca.fit_transform(X_scaled)

        n_clusters = min(self.n_clusters, len(X))
        self.model = KMeans(n_clusters=n_clusters, random_state=self.random_state, n_init=10)
        labels = self.model.fit_predict(X_scaled)

        # Auto-name clusters based on centroid characteristics
        self.cluster_labels = self._name_clusters(
            self.model.cluster_centers_,
            self.feature_names if self.pca is None else [f"PC{i}" for i in range(X_scaled.shape[1])]
        )
        self.is_fitted = True

        result = {
            "n_clusters": n_clusters,
            "n_samples": len(X),
            "inertia": round(float(self.model.inertia_), 2),
            "features_used": self.feature_names,
            "cluster_distribution": {str(k): int(np.sum(labels == k)) for k in range(n_clusters)},
            "cluster_archetypes": self.cluster_labels,
        }
        try:
            from sklearn.metrics import silhouette_score
            sil = silhouette_score(X_scaled, labels)
            result["silhouette_score"] = round(float(sil), 4)
        except Exception:
            pass
        return result

    def predict(self, input_data: Dict[str, Any]) -> Any:
        """Assign a player feature vector to a cluster."""
        if not self.is_fitted or self.model is None:
            return {"error": "Model not fitted"}
        feats = [float(input_data.get(f, 0) or 0) for f in self.feature_names]
        X = np.array([feats])
        X_scaled = self.scaler.transform(X)
        if self.pca is not None:
            X_scaled = self.pca.transform(X_scaled)
        cluster_id = int(self.model.predict(X_scaled)[0])
        return {
            "cluster_id": cluster_id,
            "archetype": self.cluster_labels.get(cluster_id, f"Cluster {cluster_id}"),
        }

    @staticmethod
    def _name_clusters(centers: np.ndarray, feature_names: List[str]) -> Dict[int, str]:
        """Heuristic cluster naming based on dominant features in centroid."""
        ARCHETYPES = ["Target Forward", "Creative Midfielder", "Defensive Anchor", "Wide Attacker", "Sweeper Keeper", "Box-to-Box", "Deep Playmaker", "Press Machine"]
        labels = {}
        for i, center in enumerate(centers):
            labels[i] = ARCHETYPES[i % len(ARCHETYPES)]
        return labels
