from typing import Any, List, Dict, Optional
from algorithms.base import MLAlgorithm
from algorithms.clustering import ClusteringAlgorithm
from algorithms.regression import RegressionAlgorithm
from algorithms.timeseries import TimeSeriesForecaster
from algorithms.anomaly import MatchPerformanceAnomalyDetector
from algorithms.role_classifier import TacticalRoleClassifier
from algorithms.fatigue import PhysicalFatiguePredictor
from algorithms.xgot import ExpectedGoalsOnTargetModel
from algorithms.pitch_control import PitchControlModel
from algorithms.expected_threat import ExpectedThreatModel
from algorithms.player_similarity import AdvancedPlayerSimilarityKNN

class AnalyticsEngine:
    """Central registry and execution engine for ML algorithms."""

    def __init__(self):
        self.algorithms: Dict[str, MLAlgorithm] = {}
        self._register_defaults()

    def _register_defaults(self):
        """Pre-register standard and football-specific ML algorithms."""
        self.register_algorithm("player_clustering", ClusteringAlgorithm(n_clusters=5))
        self.register_algorithm("goals_regression", RegressionAlgorithm(target_field="goals"))
        self.register_algorithm("shots_regression", RegressionAlgorithm(target_field="shots"))
        self.register_algorithm("form_xg_forecaster", TimeSeriesForecaster(target_field="next_xg"))
        self.register_algorithm("form_passes_forecaster", TimeSeriesForecaster(target_field="next_passes"))
        
        # New Football-Specific Models
        self.register_algorithm("performance_anomaly_detector", MatchPerformanceAnomalyDetector())
        self.register_algorithm("tactical_role_classifier", TacticalRoleClassifier(n_clusters=6))
        self.register_algorithm("fatigue_risk_predictor", PhysicalFatiguePredictor(risk_threshold=0.6))
        self.register_algorithm("xgot_finishing_model", ExpectedGoalsOnTargetModel())
        self.register_algorithm("pitch_control_nn", PitchControlModel())
        self.register_algorithm("expected_threat_model", ExpectedThreatModel())
        self.register_algorithm("advanced_player_similarity", AdvancedPlayerSimilarityKNN(n_neighbors=5))

    def register_algorithm(self, name: str, algorithm: MLAlgorithm) -> None:
        self.algorithms[name] = algorithm

    def train_model(self, name: str, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        if name not in self.algorithms:
            return {"error": f"Algorithm '{name}' not registered"}
        return self.algorithms[name].train(data)

    def train_from_mongo(self, name: str, mongodb_url: str, database: str = "scoutpro", collection: str = "player_statistics", target_field: Optional[str] = None) -> Dict[str, Any]:
        """Fetch data from MongoDB collection and train the named algorithm."""
        import pymongo
        if name not in self.algorithms:
            return {"error": f"Algorithm '{name}' not registered"}
        if target_field and hasattr(self.algorithms[name], "target_field"):
            self.algorithms[name].target_field = target_field
        client = pymongo.MongoClient(mongodb_url)
        db = client[database]
        data = list(db[collection].find({}, {"_id": 0}))
        client.close()
        if not data:
            return {"error": f"No data found in {collection}"}
        return self.algorithms[name].train(data)

    def predict(self, name: str, input_data: Dict[str, Any]) -> Any:
        if name not in self.algorithms:
            return {"error": f"Algorithm '{name}' not registered"}
        return self.algorithms[name].predict(input_data)

    def get_registered_algorithms(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": name,
                "type": type(alg).__name__,
                "fitted": getattr(alg, "is_fitted", False),
            }
            for name, alg in self.algorithms.items()
        ]
