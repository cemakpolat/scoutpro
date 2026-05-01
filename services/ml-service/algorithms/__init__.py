"""
Algorithms package for the ScoutPro ML service.
All algorithms implement the MLAlgorithm interface (train/predict on dicts).
"""

from .base import MLAlgorithm
from .clustering import ClusteringAlgorithm
from .regression import RegressionAlgorithm
from .linearreg import LinearRegressionAlgorithm
from .logisticreg import LogisticRegressionAlgorithm
from .anomaly import MatchPerformanceAnomalyDetector
from .role_classifier import TacticalRoleClassifier
from .fatigue import PhysicalFatiguePredictor
from .player_similarity import AdvancedPlayerSimilarityKNN
from .timeseries import TimeSeriesForecaster
from .xgot import ExpectedGoalsOnTargetModel
from .pitch_control import PitchControlModel
from .expected_threat import ExpectedThreatModel

__all__ = [
    "MLAlgorithm",
    "ClusteringAlgorithm",
    "RegressionAlgorithm",
    "LinearRegressionAlgorithm",
    "LogisticRegressionAlgorithm",
    "MatchPerformanceAnomalyDetector",
    "TacticalRoleClassifier",
    "PhysicalFatiguePredictor",
    "AdvancedPlayerSimilarityKNN",
    "TimeSeriesForecaster",
    "ExpectedGoalsOnTargetModel",
    "PitchControlModel",
    "ExpectedThreatModel",
]
