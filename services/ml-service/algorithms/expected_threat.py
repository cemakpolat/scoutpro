from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from .base import MLAlgorithm

logger = logging.getLogger(__name__)

# Expected Threat (xT) model.
# The pitch is divided into a grid of zones. Each zone stores:
#   - p_shoot   : probability of taking a shot from this zone
#   - p_goal    : probability that a shot from this zone results in a goal
#   - p_move    : probability of moving the ball to each other zone
#   - xT_value  : expected threat = p_shoot * p_goal + p_move * xT(destination)
#
# Training data: list of action dicts with keys
#   x, y            : pitch coordinates (0-100 scale)
#   outcome_type    : "shot", "carry", "pass"
#   end_x, end_y    : destination coordinates (for carries/passes)
#   shot_outcome    : "Goal" | other (only relevant when outcome_type=="shot")

GRID_W = 16   # columns
GRID_H = 12   # rows


def _cell(x: float, y: float) -> Tuple[int, int]:
    col = min(int(x / 100 * GRID_W), GRID_W - 1)
    row = min(int(y / 100 * GRID_H), GRID_H - 1)
    return row, col


class ExpectedThreatModel(MLAlgorithm):
    def __init__(self, grid_w: int = GRID_W, grid_h: int = GRID_H, iterations: int = 10):
        self.grid_w = grid_w
        self.grid_h = grid_h
        self.iterations = iterations
        self.is_fitted = False

        self._p_shoot = np.zeros((grid_h, grid_w))
        self._p_goal = np.zeros((grid_h, grid_w))
        self._move_matrix = np.zeros((grid_h * grid_w, grid_h * grid_w))
        self._xt_grid: Optional[np.ndarray] = None

    def _idx(self, row: int, col: int) -> int:
        return row * self.grid_w + col

    def train(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        n_cells = self.grid_h * self.grid_w
        action_count = np.zeros((self.grid_h, self.grid_w))
        shoot_count = np.zeros((self.grid_h, self.grid_w))
        goal_count = np.zeros((self.grid_h, self.grid_w))
        move_count = np.zeros((n_cells, n_cells))

        valid = 0
        for row in data:
            try:
                x = float(row.get("x", row.get("location_x", 0)))
                y = float(row.get("y", row.get("location_y", 0)))
                otype = str(row.get("outcome_type", row.get("type", ""))).lower()
            except (TypeError, ValueError):
                continue

            r, c = _cell(x, y)
            action_count[r, c] += 1
            valid += 1

            if "shot" in otype:
                shoot_count[r, c] += 1
                if str(row.get("shot_outcome", "")).lower() == "goal":
                    goal_count[r, c] += 1
            elif otype in ("carry", "pass", "dribble"):
                try:
                    ex = float(row.get("end_x", row.get("carry_end_x", x)))
                    ey = float(row.get("end_y", row.get("carry_end_y", y)))
                    er, ec = _cell(ex, ey)
                    move_count[self._idx(r, c), self._idx(er, ec)] += 1
                except (TypeError, ValueError):
                    pass

        # Normalize
        safe_ac = np.where(action_count > 0, action_count, 1)
        self._p_shoot = shoot_count / safe_ac
        self._p_goal = np.where(shoot_count > 0, goal_count / np.where(shoot_count > 0, shoot_count, 1), 0)

        row_sums = move_count.sum(axis=1, keepdims=True)
        self._move_matrix = move_count / np.where(row_sums > 0, row_sums, 1)

        # Iterative xT computation
        xt = np.zeros(n_cells)
        for _ in range(self.iterations):
            xt_grid = xt.reshape(self.grid_h, self.grid_w)
            shoot_value = self._p_shoot * self._p_goal
            move_value = (self._move_matrix @ xt).reshape(self.grid_h, self.grid_w)
            p_move = 1 - self._p_shoot
            xt = (shoot_value + p_move * move_value).flatten()

        self._xt_grid = xt.reshape(self.grid_h, self.grid_w)
        self.is_fitted = True

        return {
            "model": "expected_threat",
            "grid_size": f"{self.grid_h}x{self.grid_w}",
            "training_samples": valid,
            "iterations": self.iterations,
            "max_xt": float(self._xt_grid.max()),
            "mean_xt": float(self._xt_grid.mean()),
        }

    def predict(self, input_data: Dict[str, Any]) -> Any:
        if not self.is_fitted or self._xt_grid is None:
            return {"error": "Model not trained. Call /train/expected_threat_model first."}

        try:
            x = float(input_data.get("x", input_data.get("location_x", 0)))
            y = float(input_data.get("y", input_data.get("location_y", 0)))
        except (TypeError, ValueError):
            return {"error": "x and y coordinates are required"}

        r, c = _cell(x, y)
        xt_value = float(self._xt_grid[r, c])

        result = {
            "x": x,
            "y": y,
            "grid_cell": {"row": r, "col": c},
            "expected_threat": round(xt_value, 6),
            "model": "expected_threat",
        }

        # If end coordinates supplied, also compute xT gained
        try:
            ex = float(input_data["end_x"])
            ey = float(input_data["end_y"])
            er, ec = _cell(ex, ey)
            end_xt = float(self._xt_grid[er, ec])
            result["end_expected_threat"] = round(end_xt, 6)
            result["xt_gained"] = round(end_xt - xt_value, 6)
        except (KeyError, TypeError, ValueError):
            pass

        return result
