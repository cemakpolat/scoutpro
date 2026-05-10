from typing import Any, Dict, List

from algorithms.base import MLAlgorithm


class MarketValueEstimator(MLAlgorithm):
    """Heuristic transfer-value estimator backed by football production signals."""

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
    def _position_group(position: Any) -> str:
        normalized = str(position or '').strip().lower()
        if not normalized:
            return 'outfield'
        if normalized in {'gk', 'goalkeeper', 'keeper'} or 'goalkeeper' in normalized:
            return 'goalkeeper'
        if any(token in normalized for token in ('cb', 'centre-back', 'center-back', 'defender', 'fullback', 'left back', 'right back', 'wing-back', 'wing back')):
            return 'defender'
        if any(token in normalized for token in ('dm', 'cm', 'am', 'midfield', 'midfielder')):
            return 'midfielder'
        if any(token in normalized for token in ('winger', 'forward', 'striker', 'attacker', 'centre-forward', 'center-forward', 'cf')):
            return 'forward'
        return 'outfield'

    @classmethod
    def _prime_window(cls, position: Any) -> tuple[int, int]:
        group = cls._position_group(position)
        windows = {
            'goalkeeper': (28, 33),
            'defender': (25, 30),
            'midfielder': (24, 29),
            'forward': (23, 28),
            'outfield': (24, 29),
        }
        return windows.get(group, (24, 29))

    def train(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        return {
            'status': 'success',
            'samples': len(data),
            'message': 'Pre-configured market value estimator is ready',
        }

    def predict(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        position = input_data.get('position') or input_data.get('detailed_position')
        position_group = self._position_group(position)
        age = self._to_float(input_data.get('age'), 24.0)
        minutes_played = self._to_float(input_data.get('minutes_played'))
        matches_played = self._to_float(input_data.get('matches_played'))
        goals = self._to_float(input_data.get('goals'))
        assists = self._to_float(input_data.get('assists'))
        total_xg = self._to_float(input_data.get('total_xg'))
        progressive_passes = self._to_float(input_data.get('progressive_passes'))
        key_passes = self._to_float(input_data.get('key_passes'))
        pressures = self._to_float(input_data.get('pressures'))
        tackles = self._to_float(input_data.get('tackles'))
        interceptions = self._to_float(input_data.get('interceptions'))
        pass_accuracy = self._to_float(input_data.get('pass_accuracy'))
        contract_years_remaining = max(0.0, self._to_float(input_data.get('contract_years_remaining'), 2.0))

        prime_start, prime_end = self._prime_window(position)
        if age < prime_start:
            age_factor = 0.82 + max(0.0, age - 17.0) * 0.04
        elif age <= prime_end:
            age_factor = 1.16
        else:
            age_factor = max(0.58, 1.16 - (age - prime_end) * 0.08)

        position_factor = {
            'forward': 1.18,
            'midfielder': 1.04,
            'defender': 0.92,
            'goalkeeper': 0.78,
            'outfield': 1.0,
        }.get(position_group, 1.0)
        availability_factor = min(1.22, 0.62 + min(minutes_played, 3200.0) / 3200.0 * 0.60)
        contract_factor = 0.82 + min(contract_years_remaining, 5.0) * 0.09
        production_score = (
            goals * 1.8
            + assists * 1.35
            + total_xg * 1.05
            + progressive_passes * 0.06
            + key_passes * 0.22
            + pressures * 0.015
            + tackles * 0.04
            + interceptions * 0.05
            + pass_accuracy * 0.035
        )
        estimate = round(
            max(0.5, (1.25 + production_score) * age_factor * position_factor * availability_factor * contract_factor / 2.0),
            2,
        )

        present_fields = [
            age,
            minutes_played,
            matches_played,
            goals,
            assists,
            total_xg,
            progressive_passes,
            key_passes,
            pass_accuracy,
        ]
        completeness = sum(1 for value in present_fields if value not in (None, 0, 0.0)) / len(present_fields)
        confidence = round(min(88.0, 48.0 + completeness * 24.0 + min(minutes_played, 3200.0) / 3200.0 * 16.0), 1)

        if estimate < 5:
            band = 'developmental'
        elif estimate < 15:
            band = 'established'
        elif estimate < 30:
            band = 'premium-starter'
        else:
            band = 'elite-asset'

        return {
            'estimateMillionEUR': estimate,
            'displayValue': f'EUR {estimate:.1f}m',
            'band': band,
            'confidence': confidence,
            'factors': {
                'age': round(age, 1),
                'positionGroup': position_group,
                'primeWindow': {'start': prime_start, 'end': prime_end},
                'contractYearsRemaining': round(contract_years_remaining, 2),
            },
            'model': 'market_value_estimator',
        }