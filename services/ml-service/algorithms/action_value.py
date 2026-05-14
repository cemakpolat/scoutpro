from typing import Any, Dict, List, Optional, Tuple

from algorithms.base import MLAlgorithm
from algorithms.persisted_regressor import PersistedDictRegressor


class VaepActionValueModel(MLAlgorithm):
    """Supervised VAEP regressor with heuristic explainability fallback."""

    TARGET_FIELDS = (
        'vaep_value',
        'vaepValue',
        'action_value',
        'actionValue',
        'value_added',
        'expected_possession_value',
    )

    def __init__(self, model_path: Optional[str] = None, min_samples: int = 32):
        self.target_field: Optional[str] = None
        self.regressor = PersistedDictRegressor(
            model_name='vaep_action_model',
            artifact_path=model_path,
            min_samples=min_samples,
            registry_thresholds={
                'staging_min_r2': 0.2,
                'production_min_r2': 0.4,
            },
        )
        self.is_fitted = self.regressor.is_fitted
        self.metrics = dict(self.regressor.metrics)

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

    def _build_feature_row(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        action_type = str(input_data.get('type_name') or input_data.get('type') or '').strip().lower() or 'unknown'
        start_x = self._to_float(input_data.get('x', input_data.get('location_x', 0.0)))
        start_y = self._to_float(input_data.get('y', input_data.get('location_y', 50.0)))
        end_x = self._to_float(input_data.get('end_x', input_data.get('carry_end_x', start_x)), start_x)
        end_y = self._to_float(input_data.get('end_y', input_data.get('carry_end_y', start_y)), start_y)
        territory_gain = max(0.0, self._zone_value(end_x, end_y) - self._zone_value(start_x, start_y))

        return {
            'action_type': action_type,
            'start_x': start_x,
            'start_y': start_y,
            'end_x': end_x,
            'end_y': end_y,
            'delta_x': round(end_x - start_x, 4),
            'delta_y': round(end_y - start_y, 4),
            'success': 1 if self._is_truthy(input_data.get('is_successful', input_data.get('successful', True))) else 0,
            'xg_value': self._to_float(input_data.get('xg_value', input_data.get('analytical_xg', 0.0))),
            'territory_gain': round(territory_gain, 4),
            'progressive_action': 1 if (self._is_truthy(input_data.get('progressive_pass')) or self._is_truthy(input_data.get('progressive_carry'))) else 0,
            'entered_final_third': 1 if self._is_truthy(input_data.get('entered_final_third')) else 0,
            'entered_box': 1 if self._is_truthy(input_data.get('entered_box')) else 0,
            'is_key_pass': 1 if self._is_truthy(input_data.get('is_key_pass')) else 0,
            'is_assist': 1 if self._is_truthy(input_data.get('is_assist')) else 0,
            'is_goal': 1 if self._is_truthy(input_data.get('is_goal')) else 0,
            'high_regain': 1 if self._is_truthy(input_data.get('high_regain')) else 0,
        }

    def _extract_training_target(self, row: Dict[str, Any]) -> Tuple[Optional[float], Optional[str]]:
        target_fields = [self.target_field] if self.target_field else list(self.TARGET_FIELDS)
        for field_name in target_fields:
            if not field_name or field_name not in row:
                continue
            try:
                return float(row.get(field_name)), field_name
            except (TypeError, ValueError):
                continue
        return None, None

    def _heuristic_components(self, input_data: Dict[str, Any]) -> Tuple[str, float, Dict[str, float]]:
        feature_row = self._build_feature_row(input_data)
        action_type = str(feature_row['action_type'])
        start_threat = self._zone_value(float(feature_row['start_x']), float(feature_row['start_y']))
        end_threat = self._zone_value(float(feature_row['end_x']), float(feature_row['end_y']))
        territory_gain = max(0.0, end_threat - start_threat)

        offensive_value = 0.0
        defensive_value = 0.0
        turnover_penalty = 0.0

        if action_type in {'pass', 'cross', 'carry', 'dribble'}:
            offensive_value += territory_gain if int(feature_row['success']) else territory_gain * -0.45
            if int(feature_row['progressive_action']):
                offensive_value += 0.08
            if int(feature_row['entered_final_third']):
                offensive_value += 0.05
            if int(feature_row['entered_box']):
                offensive_value += 0.14
            if int(feature_row['is_key_pass']):
                offensive_value += 0.12
            if int(feature_row['is_assist']):
                offensive_value += 0.22
            if not int(feature_row['success']) and start_threat >= 0.55:
                turnover_penalty -= 0.12

        if 'shot' in action_type or float(feature_row['xg_value']) > 0 or int(feature_row['is_goal']):
            offensive_value += max(float(feature_row['xg_value']), territory_gain)
            if int(feature_row['is_goal']):
                offensive_value += 0.75

        if action_type in {'tackle', 'interception', 'recovery', 'ball recovery', 'pressure'}:
            defensive_value += 0.08
            if action_type in {'tackle', 'interception', 'recovery', 'ball recovery'}:
                defensive_value += 0.04
            if int(feature_row['high_regain']):
                defensive_value += 0.06
            if int(feature_row['success']):
                defensive_value += 0.03

        total_value = round(offensive_value + defensive_value + turnover_penalty, 4)
        return action_type, total_value, {
            'territoryGain': round(territory_gain, 4),
            'offensiveValue': round(offensive_value, 4),
            'defensiveValue': round(defensive_value, 4),
            'turnoverPenalty': round(turnover_penalty, 4),
        }

    def _trained_confidence(self, feature_row: Dict[str, Any]) -> float:
        completeness = sum(1 for value in feature_row.values() if value not in (None, '', 0, 0.0, 'unknown')) / len(feature_row)
        r2_value = max(0.0, float(self.metrics.get('r2_score', 0.0) or 0.0))
        mae = abs(float(self.metrics.get('mae', 0.0) or 0.0))
        confidence = 58.0 + completeness * 18.0 + min(r2_value, 1.0) * 14.0 - min(mae * 60.0, 12.0)
        return round(max(50.0, min(94.0, confidence)), 1)

    def train(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        rows: List[Tuple[Dict[str, Any], float]] = []
        target_field_used: Optional[str] = None

        for row in data:
            target_value, target_field = self._extract_training_target(row)
            if target_value is None:
                continue
            rows.append((self._build_feature_row(row), target_value))
            if target_field and not target_field_used:
                target_field_used = target_field

        result = self.regressor.fit_rows(rows, target_field_used or self.target_field or 'vaep_value')
        self.is_fitted = self.regressor.is_fitted
        self.metrics = dict(self.regressor.metrics)
        if 'error' in result:
            return result
        return {
            **result,
            'message': 'Supervised VAEP action value model trained successfully',
        }

    def predict(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        feature_row = self._build_feature_row(input_data)
        action_type, heuristic_value, heuristic_components = self._heuristic_components(input_data)
        trained_prediction = self.regressor.predict_value(feature_row)
        self.is_fitted = self.regressor.is_fitted
        self.metrics = dict(self.regressor.metrics)

        if trained_prediction is None:
            return {
                'action_type': action_type or 'unknown',
                'vaepValue': heuristic_value,
                'components': heuristic_components,
                'confidence': 72.0,
                'predictionSource': 'heuristic_fallback',
                'modelDeploymentSource': self.regressor.active_model_source,
                'modelRegistryStage': self.regressor.registry_stage,
                'model': 'vaep_action_model',
            }

        trained_value = round(trained_prediction, 4)
        return {
            'action_type': action_type or 'unknown',
            'vaepValue': trained_value,
            'components': {
                **heuristic_components,
                'heuristicBaseline': heuristic_value,
                'learnedAdjustment': round(trained_value - heuristic_value, 4),
            },
            'confidence': self._trained_confidence(feature_row),
            'predictionSource': 'trained_model',
            'modelDeploymentSource': self.regressor.active_model_source,
            'modelRegistryStage': self.regressor.registry_stage,
            'model': 'vaep_action_model',
        }