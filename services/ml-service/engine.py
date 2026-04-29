from typing import Dict, Any, List
from .algorithms.base import MLAlgorithm

class AnalyticsEngine:
    def __init__(self):
        # Registry mapping model names to MLAlgorithm instances
        self.algorithms: Dict[str, MLAlgorithm] = {}

    def register_algorithm(self, name: str, algorithm: MLAlgorithm) -> None:
        """Register a new ML algorithm under a specific name."""
        self.algorithms[name] = algorithm

    def train_model(self, name: str, data: List[Dict[str, Any]]) -> None:
        """Train a registered model by name with the given generic domain data."""
        if name not in self.algorithms:
            raise ValueError(f"Algorithm '{name}' not registered in AnalyticsEngine.")
        self.algorithms[name].train(data)

    def predict(self, name: str, input_data: Dict[str, Any]) -> Any:
        """Generate a prediction using a registered model."""
        if name not in self.algorithms:
            raise ValueError(f"Algorithm '{name}' not registered in AnalyticsEngine.")
        return self.algorithms[name].predict(input_data)
