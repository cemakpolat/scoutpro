from typing import Any, Dict, List

from algorithms.base import MLAlgorithm


class VaepActionValueModel(MLAlgorithm):
    """Heuristic VAEP-style action valuation for single event inference."""

    def __init__(self):
        self.is_fitted = True

    @staticmethod
    def _to_float(value: Any, default: float = 0.0) -> float:
        if value in (None, '', 'None'):
            return default
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _is_truthy(value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value != 0
        return str(value or '').strip().lower() in {'1', 'true', 'yes', 'y', 'on'}

    @staticmethod
    def _zone_value(x: float, y: float) -> float:
        clamped_x = max(0.0, min(100.0, x))
        clamped_y = max(0.0, min(100.0, y))
        centrality = max(0.0, 1.0 - abs(clamped_y - 50.0) / 50.0)
        return round((clamped_x / 100.0) * 0.72 + centrality * 0.18, 4)

    def train(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        return {
            'status': 'success',
            'samples': len(data),
            'message': 'Pre-configured VAEP-style action value model is ready',
        }

    def predict(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        action_type = str(input_data.get('type_name') or input_data.get('type') or '').strip().lower()
        start_x = self._to_float(input_data.get('x', input_data.get('location_x', 0.0)))
        start_y = self._to_float(input_data.get('y', input_data.get('location_y', 50.0)))
        end_x = self._to_float(input_data.get('end_x', input_data.get('carry_end_x', start_x)), start_x)
        end_y = self._to_float(input_data.get('end_y', input_data.get('carry_end_y', start_y)), start_y)
        success = self._is_truthy(input_data.get('is_successful', input_data.get('successful', True)))
        xg_value = self._to_float(input_data.get('xg_value', input_data.get('analytical_xg', 0.0)))

        start_threat = self._zone_value(start_x, start_y)
        end_threat = self._zone_value(end_x, end_y)
        territory_gain = max(0.0, end_threat - start_threat)

        offensive_value = 0.0
        defensive_value = 0.0
        turnover_penalty = 0.0

        if action_type in {'pass', 'cross', 'carry', 'dribble'}:
            offensive_value += territory_gain if success else territory_gain * -0.45
            if self._is_truthy(input_data.get('progressive_pass')) or self._is_truthy(input_data.get('progressive_carry')):
                offensive_value += 0.08
            if self._is_truthy(input_data.get('entered_final_third')):
                offensive_value += 0.05
            if self._is_truthy(input_data.get('entered_box')):
                offensive_value += 0.14
            if self._is_truthy(input_data.get('is_key_pass')):
                offensive_value += 0.12
            if self._is_truthy(input_data.get('is_assist')):
                offensive_value += 0.22
            if not success and start_threat >= 0.55:
                turnover_penalty -= 0.12

        if 'shot' in action_type or xg_value > 0 or self._is_truthy(input_data.get('is_goal')):
            offensive_value += max(xg_value, territory_gain)
            if self._is_truthy(input_data.get('is_goal')):
                offensive_value += 0.75

        if action_type in {'tackle', 'interception', 'recovery', 'ball recovery', 'pressure'}:
            defensive_value += 0.08
            if action_type in {'tackle', 'interception', 'recovery', 'ball recovery'}:
                defensive_value += 0.04
            if self._is_truthy(input_data.get('high_regain')):
                defensive_value += 0.06
            if success:
                defensive_value += 0.03

        total_value = round(offensive_value + defensive_value + turnover_penalty, 4)

        return {
            'action_type': action_type or 'unknown',
            'vaepValue': total_value,
            'components': {
                'territoryGain': round(territory_gain, 4),
                'offensiveValue': round(offensive_value, 4),
                'defensiveValue': round(defensive_value, 4),
                'turnoverPenalty': round(turnover_penalty, 4),
            },
            'model': 'vaep_action_model',
        }