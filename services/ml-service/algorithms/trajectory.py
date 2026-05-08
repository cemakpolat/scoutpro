from typing import Dict, Any, List, Optional
import numpy as np
from algorithms.base import MLAlgorithm
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class PlayerTrajectoryModel(MLAlgorithm):
    """
    Analyzes historical time-series data to cluster a player across consecutive
    seasons and forecasts their likely developmental path (cluster).
    """

    def __init__(self):
        self.is_fitted = True
        self.clusters = {
            0: "Developmental Prospect",
            1: "Rotation Player",
            2: "Starter",
            3: "Key Player",
            4: "Star/Elite"
        }
        
        # Simple transition matrix for Markov Chain (mock probabilities)
        # Rows: current state, Cols: next state
        # Probabilities of staying in same state or moving up/down
        self.transition_matrix = np.array([
            [0.4, 0.4, 0.1, 0.05, 0.05], # Prospect -> 
            [0.1, 0.5, 0.3, 0.1, 0.0],   # Rotation -> 
            [0.05, 0.1, 0.6, 0.2, 0.05], # Starter -> 
            [0.0, 0.05, 0.15, 0.6, 0.2], # Key Player ->
            [0.0, 0.0, 0.05, 0.15, 0.8]  # Elite ->
        ])

    def train(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        In a real system, this would learn the transition matrix and 
        cluster definitions from historical longitudinal data.
        """
        return {"status": "success", "message": "Pre-trained model loaded"}

    def _determine_cluster(self, metrics: Dict[str, Any]) -> int:
        """
        Map a season's metrics to a cluster.
        Simplified heuristic for demonstration.
        """
        score = metrics.get('minutes_played', 0) / 3000 * 2.0
        score += metrics.get('xg_chain', 0) * 1.5
        score += metrics.get('defensive_actions', 0) * 0.5
        
        if score < 0.8: return 0
        if score < 1.5: return 1
        if score < 2.5: return 2
        if score < 3.5: return 3
        return 4

    def predict(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Forecast the player's trajectory.
        Input: Time-series of past 3-5 seasons metrics.
        Returns: Historical clusters + 2 season forecast.
        """
        historical_seasons = input_data.get('history', [])
        if not historical_seasons:
            return {"error": "No historical data provided for trajectory."}
            
        # 1. Map history to clusters
        history_mapped = []
        last_state = 0
        
        for season in historical_seasons:
            state = self._determine_cluster(season.get('metrics', {}))
            history_mapped.append({
                "period": season.get('period', 'Unknown'),
                "cluster_id": state,
                "cluster_name": self.clusters[state],
                "metrics_snapshot": season.get('metrics', {})
            })
            last_state = state
            
        # 2. Forecast next 2 seasons (Markov Chain)
        forecast = []
        current_state_probs = np.zeros(len(self.clusters))
        current_state_probs[last_state] = 1.0
        
        # Forecast Season N+1
        next_state_probs_1 = np.dot(current_state_probs, self.transition_matrix)
        likely_state_1 = int(np.argmax(next_state_probs_1))
        forecast.append({
            "forecast_period": "Season N+1",
            "predicted_cluster_id": likely_state_1,
            "predicted_cluster_name": self.clusters[likely_state_1],
            "confidence_distribution": {self.clusters[i]: round(float(prob), 3) for i, prob in enumerate(next_state_probs_1)}
        })
        
        # Forecast Season N+2
        next_state_probs_2 = np.dot(next_state_probs_1, self.transition_matrix)
        likely_state_2 = int(np.argmax(next_state_probs_2))
        forecast.append({
            "forecast_period": "Season N+2",
            "predicted_cluster_id": likely_state_2,
            "predicted_cluster_name": self.clusters[likely_state_2],
            "confidence_distribution": {self.clusters[i]: round(float(prob), 3) for i, prob in enumerate(next_state_probs_2)}
        })
        
        return {
            "player_id": input_data.get('player_id'),
            "historical_trajectory": history_mapped,
            "forecast": forecast,
            "baseline_peers": self._get_comparable_baselines(last_state)
        }
        
    def _get_comparable_baselines(self, current_cluster: int) -> List[Dict[str, Any]]:
        """Mock out baseline peers that followed this trajectory"""
        return [
            {"player_id": "mock_peer_1", "name": "Comparable Player A", "similarity_score": 0.89},
            {"player_id": "mock_peer_2", "name": "Comparable Player B", "similarity_score": 0.85}
        ]
