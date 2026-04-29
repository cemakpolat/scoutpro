from abc import ABC, abstractmethod
from typing import Any, List, Dict

class MLAlgorithm(ABC):
    def __init__(self):
        pass
    @abstractmethod
    def train(self, data: List[Dict[str, Any]]) -> None:
        """
        Train the machine learning model with the provided data.
        Data is expected to be a list of domain entity dictionaries.
        """
        pass

    @abstractmethod
    def predict(self, input_data: Dict[str, Any]) -> Any:
        """
        Generate predictions using the trained model.
        Input data is expected to be a dictionary representing a domain entity's features.
        """
        pass
