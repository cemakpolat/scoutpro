import numpy as np
import logging
from typing import Dict, Any, List
from algorithms.base import MLAlgorithm

try:
    from sklearn.neighbors import NearestNeighbors
    from sklearn.preprocessing import StandardScaler
except ImportError:
    NearestNeighbors = None
    StandardScaler = None

logger = logging.getLogger(__name__)

class AdvancedPlayerSimilarityKNN(MLAlgorithm):
    """
    K-Nearest Neighbors approach for scouting. Finds the most statistically 
    similar players based on a complex multidimensional feature space.
    """
    def __init__(self, n_neighbors: int = 5):
        self.n_neighbors = n_neighbors
        self.model = NearestNeighbors(n_neighbors=self.n_neighbors, algorithm='auto', metric='cosine') if NearestNeighbors else None
        self.scaler = StandardScaler() if StandardScaler else None
        self.is_fitted = False
        self.reference_ids = []

    def train(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        data should be a list of player aggregates.
        e.g. {'player_id': 123, 'passes_p90': 45.2, 'tackles_p90': 2.1, ...}
        """
        if not self.model or not self.scaler:
            return {"error": "Scikit-Learn KNN/StandardScaler not installed."}

        X = []
        self.reference_ids = []
        
        # Define a consistent feature order
        feature_keys = ['passes_p90', 'pass_accuracy', 'shots_p90', 'xg_p90', 
                        'recoveries_p90', 'interceptions_p90', 'progressive_carries_p90']

        for record in data:
            if 'player_id' in record:
                self.reference_ids.append(record['player_id'])
                features = [float(record.get(k, 0.0)) for k in feature_keys]
                X.append(features)

        if len(X) < self.n_neighbors:
            return {"error": f"Needs at least {self.n_neighbors} players in database."}

        X_scaled = self.scaler.fit_transform(np.array(X))
        self.model.fit(X_scaled)
        self.is_fitted = True

        return {"status": "success", "samples": len(X), "algorithm": "KNN_Similarity"}

    def predict(self, input_data: Dict[str, Any]) -> Any:
        if not self.is_fitted or not self.model:
            return {"error": "Similarity model is not fitted."}

        try:
            # We can either pass an ID (if we cached data) or raw stats
            feature_keys = ['passes_p90', 'pass_accuracy', 'shots_p90', 'xg_p90', 
                            'recoveries_p90', 'interceptions_p90', 'progressive_carries_p90']
            
            features = [float(input_data.get(k, 0.0)) for k in feature_keys]
            x_input = np.array(features).reshape(1, -1)
            x_scaled = self.scaler.transform(x_input)
            
            distances, indices = self.model.kneighbors(x_scaled, n_neighbors=self.n_neighbors)
            
            similar_players = []
            for i, idx in enumerate(indices[0]):
                similarity_score = 1.0 - distances[0][i] # Cosine similarity (1 - distance)
                similar_players.append({
                    "player_id": self.reference_ids[idx],
                    "similarity_score": round(similarity_score * 100, 2)
                })

            return {
                "input_stats": input_data,
                "matches": similar_players
            }
        except Exception as e:
            logger.error(f"Similarity prediction error: {e}")
            return {"error": str(e)}
