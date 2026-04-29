"""
Algorithms package exports for the ML service.

This module exposes the stable, engine-compatible algorithm classes
implemented in this package. Legacy or third-party algorithm files
that are not part of the `MLAlgorithm` interface should not be
exported here to avoid accidental imports.
"""

from .clustering import ClusteringAlgorithm
from .regression import RegressionAlgorithm
from .linearreg import LinearRegressionAlgorithm
try:
	from .logisticreg import LogisticRegressionAlgorithm
except Exception:
	# optional/legacy file may be missing in some worktrees
	LogisticRegressionAlgorithm = None

__all__ = [
	"ClusteringAlgorithm",
	"RegressionAlgorithm",
	"LinearRegressionAlgorithm",
	"LogisticRegressionAlgorithm",
]
