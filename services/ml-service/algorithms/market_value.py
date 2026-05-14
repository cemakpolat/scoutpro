import math
import re
from typing import Any, Dict, List, Optional, Tuple

from algorithms.base import MLAlgorithm
from algorithms.persisted_regressor import PersistedDictRegressor


class MarketValueEstimator(MLAlgorithm):
    """Supervised market-value estimator with persisted training artifacts and heuristic fallback."""

    TARGET_FIELDS = (
        'market_value_eur',
        'market_value',
        'marketValue',
        'market_value_million_eur',
        'estimated_market_value',
        'estimated_market_value_eur',
        'estimatedMarketValue',
        'transfer_value',
        'transfer_value_eur',
        'value_eur',
        'current_value',
    )

    def __init__(self, model_path: Optional[str] = None, min_samples: int = 24):
        self.target_field: Optional[str] = None
        self.regressor = PersistedDictRegressor(
            model_name='market_value_estimator',
            artifact_path=model_path,
            min_samples=min_samples,
            registry_thresholds={
                'staging_min_r2': 0.3,
                'production_min_r2': 0.55,
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

    @staticmethod
    def _player_candidate_ids(row: Dict[str, Any]) -> List[str]:
        candidates: List[str] = []

        def add(candidate: Any) -> None:
            if candidate in (None, '', 'None'):
                return
            normalized = str(candidate).strip()
            if normalized and normalized not in candidates:
                candidates.append(normalized)

        provider_ids = row.get('provider_ids') or {}
        if isinstance(provider_ids, dict):
            add(provider_ids.get('opta'))

        add(row.get('id'))
        add(row.get('player_id'))
        add(row.get('playerId'))
        add(row.get('playerID'))
        add(row.get('uID'))
        return candidates

    @staticmethod
    def _availability_factor(minutes_played: float) -> float:
        return min(1.22, 0.62 + min(minutes_played, 3200.0) / 3200.0 * 0.60)

    @staticmethod
    def _contract_factor(contract_years_remaining: float) -> float:
        return 0.82 + min(contract_years_remaining, 5.0) * 0.09

    @staticmethod
    def _band_for_value(estimate: float) -> str:
        if estimate < 5:
            return 'developmental'
        if estimate < 15:
            return 'established'
        if estimate < 30:
            return 'premium-starter'
        return 'elite-asset'

    @staticmethod
    def _market_value_from_string(value: str) -> Optional[float]:
        normalized = value.strip().lower().replace('eur', '').replace('€', '').replace(',', '')
        if not normalized:
            return None

        match = re.search(r'-?\d+(?:\.\d+)?', normalized)
        if not match:
            return None

        amount = float(match.group())
        if 'bn' in normalized or 'billion' in normalized:
            return amount * 1000.0
        if 'm' in normalized or 'million' in normalized:
            return amount
        if 'k' in normalized or 'thousand' in normalized:
            return amount / 1000.0
        return amount / 1_000_000 if abs(amount) >= 1000 else amount

    @classmethod
    def _market_value_millions(cls, value: Any, field_name: str = '') -> Optional[float]:
        if value in (None, '', 'None'):
            return None
        if isinstance(value, str):
            parsed = cls._market_value_from_string(value)
            return parsed if parsed and parsed > 0 else None
        try:
            amount = float(value)
        except (TypeError, ValueError):
            return None

        if not math.isfinite(amount) or amount <= 0:
            return None

        normalized_field = field_name.lower()
        if 'million' in normalized_field:
            return amount
        if 'eur' in normalized_field and abs(amount) >= 1000:
            return amount / 1_000_000
        return amount / 1_000_000 if abs(amount) >= 1000 else amount

    def _extract_training_target(self, row: Dict[str, Any]) -> Tuple[Optional[float], Optional[str]]:
        target_fields = [self.target_field] if self.target_field else list(self.TARGET_FIELDS)
        for field_name in target_fields:
            if not field_name or field_name not in row:
                continue
            parsed = self._market_value_millions(row.get(field_name), field_name)
            if parsed is not None:
                return parsed, field_name
        return None, None

    def _build_feature_row(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        position = input_data.get('position') or input_data.get('detailed_position') or input_data.get('detailedPosition')
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
        prime_distance = 0.0
        if age < prime_start:
            prime_distance = age - prime_start
        elif age > prime_end:
            prime_distance = age - prime_end

        per_90_factor = 90.0 / minutes_played if minutes_played > 0 else 0.0
        return {
            'position_group': position_group,
            'position_label': str(position or 'unknown').strip().lower() or 'unknown',
            'age': age,
            'prime_start': float(prime_start),
            'prime_end': float(prime_end),
            'prime_distance': round(prime_distance, 2),
            'minutes_played': minutes_played,
            'matches_played': matches_played,
            'availability_factor': round(self._availability_factor(minutes_played), 4),
            'goals': goals,
            'assists': assists,
            'total_xg': total_xg,
            'progressive_passes': progressive_passes,
            'key_passes': key_passes,
            'pressures': pressures,
            'tackles': tackles,
            'interceptions': interceptions,
            'pass_accuracy': pass_accuracy,
            'contract_years_remaining': contract_years_remaining,
            'contract_factor': round(self._contract_factor(contract_years_remaining), 4),
            'goals_per90': round(goals * per_90_factor, 4),
            'assists_per90': round(assists * per_90_factor, 4),
            'xg_per90': round(total_xg * per_90_factor, 4),
            'progressive_passes_per90': round(progressive_passes * per_90_factor, 4),
            'key_passes_per90': round(key_passes * per_90_factor, 4),
            'pressures_per90': round(pressures * per_90_factor, 4),
            'tackles_per90': round(tackles * per_90_factor, 4),
            'interceptions_per90': round(interceptions * per_90_factor, 4),
        }

    def _heuristic_prediction(self, feature_row: Dict[str, Any]) -> Dict[str, Any]:
        position_group = str(feature_row['position_group'])
        age = float(feature_row['age'])
        minutes_played = float(feature_row['minutes_played'])
        goals = float(feature_row['goals'])
        assists = float(feature_row['assists'])
        total_xg = float(feature_row['total_xg'])
        progressive_passes = float(feature_row['progressive_passes'])
        key_passes = float(feature_row['key_passes'])
        pressures = float(feature_row['pressures'])
        tackles = float(feature_row['tackles'])
        interceptions = float(feature_row['interceptions'])
        pass_accuracy = float(feature_row['pass_accuracy'])
        contract_years_remaining = float(feature_row['contract_years_remaining'])
        prime_start = int(feature_row['prime_start'])
        prime_end = int(feature_row['prime_end'])

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
        availability_factor = self._availability_factor(minutes_played)
        contract_factor = self._contract_factor(contract_years_remaining)
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

        completeness_features = [
            age,
            minutes_played,
            float(feature_row['matches_played']),
            goals,
            assists,
            total_xg,
            progressive_passes,
            key_passes,
            pass_accuracy,
        ]
        completeness = sum(1 for value in completeness_features if value not in (None, 0, 0.0)) / len(completeness_features)
        confidence = round(min(88.0, 48.0 + completeness * 24.0 + min(minutes_played, 3200.0) / 3200.0 * 16.0), 1)

        return {
            'estimateMillionEUR': estimate,
            'displayValue': f'EUR {estimate:.1f}m',
            'band': self._band_for_value(estimate),
            'confidence': confidence,
            'factors': {
                'age': round(age, 1),
                'positionGroup': position_group,
                'primeWindow': {'start': prime_start, 'end': prime_end},
                'contractYearsRemaining': round(contract_years_remaining, 2),
            },
            'model': 'market_value_estimator',
            'predictionSource': 'heuristic_fallback',
            'trainedModelAvailable': False,
            'modelDeploymentSource': self.regressor.active_model_source,
            'modelRegistryStage': self.regressor.registry_stage,
        }

    def _trained_confidence(self, feature_row: Dict[str, Any]) -> float:
        completeness_features = [
            feature_row.get('age'),
            feature_row.get('minutes_played'),
            feature_row.get('matches_played'),
            feature_row.get('goals'),
            feature_row.get('assists'),
            feature_row.get('total_xg'),
            feature_row.get('progressive_passes'),
            feature_row.get('key_passes'),
            feature_row.get('pass_accuracy'),
        ]
        completeness = sum(1 for value in completeness_features if value not in (None, 0, 0.0)) / len(completeness_features)
        r2_value = max(0.0, float(self.metrics.get('r2_score', 0.0) or 0.0))
        mae = abs(float(self.metrics.get('mae', 0.0) or 0.0))
        confidence = 63.0 + completeness * 18.0 + min(r2_value, 1.0) * 16.0 - min(mae * 1.8, 12.0)
        return round(max(55.0, min(96.0, confidence)), 1)

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

        result = self.regressor.fit_rows(rows, target_field_used or self.target_field or 'market_value')
        self.is_fitted = self.regressor.is_fitted
        self.metrics = dict(self.regressor.metrics)
        if 'error' in result:
            return result
        return {
            **result,
            'message': 'Supervised market value estimator trained successfully',
        }

    def train_from_mongo(
        self,
        mongodb_url: str,
        database: str = 'scoutpro',
        collection: str = 'player_statistics',
        target_field: Optional[str] = None,
    ) -> Dict[str, Any]:
        import pymongo

        if target_field:
            self.target_field = target_field

        client = pymongo.MongoClient(mongodb_url)
        try:
            db = client[database]
            players = list(db['players'].find({}, {'_id': 0}))
            stats_docs = list(db[collection].find({}, {'_id': 0}))
        finally:
            client.close()

        stats_by_player_id: Dict[str, Dict[str, Any]] = {}
        for stats_doc in stats_docs:
            for candidate_id in self._player_candidate_ids(stats_doc):
                stats_by_player_id.setdefault(candidate_id, stats_doc)

        merged_rows: List[Dict[str, Any]] = []
        for player in players:
            merged = dict(player)
            for candidate_id in self._player_candidate_ids(player):
                matched_stats = stats_by_player_id.get(candidate_id)
                if matched_stats:
                    merged.update(matched_stats)
                    break

            target_value, _ = self._extract_training_target(merged)
            if target_value is not None:
                merged_rows.append(merged)

        if not merged_rows:
            return {
                'error': 'No labeled market value training rows found across players and statistics collections',
                'n_samples': 0,
            }

        result = self.train(merged_rows)
        if 'error' not in result:
            result['source_collection'] = collection
            result['joined_player_rows'] = len(merged_rows)
        return result

    def predict(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        feature_row = self._build_feature_row(input_data)
        fallback = self._heuristic_prediction(feature_row)
        trained_prediction = self.regressor.predict_value(feature_row)
        self.is_fitted = self.regressor.is_fitted
        self.metrics = dict(self.regressor.metrics)

        if trained_prediction is None:
            return fallback

        estimate = round(max(0.5, trained_prediction), 2)
        prime_start = int(feature_row['prime_start'])
        prime_end = int(feature_row['prime_end'])
        return {
            'estimateMillionEUR': estimate,
            'displayValue': f'EUR {estimate:.1f}m',
            'band': self._band_for_value(estimate),
            'confidence': self._trained_confidence(feature_row),
            'factors': {
                'age': round(float(feature_row['age']), 1),
                'positionGroup': feature_row['position_group'],
                'primeWindow': {'start': prime_start, 'end': prime_end},
                'contractYearsRemaining': round(float(feature_row['contract_years_remaining']), 2),
                'trainingMetrics': {
                    'mae': self.metrics.get('mae'),
                    'r2_score': self.metrics.get('r2_score'),
                    'samples': self.metrics.get('samples'),
                },
            },
            'model': 'market_value_estimator',
            'predictionSource': 'trained_model',
            'trainedModelAvailable': True,
            'modelDeploymentSource': self.regressor.active_model_source,
            'modelRegistryStage': self.regressor.registry_stage,
        }