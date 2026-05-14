import unittest
from tempfile import TemporaryDirectory
from pathlib import Path

from algorithms.action_value import VaepActionValueModel
from algorithms.market_value import MarketValueEstimator
from models.predictor import XGModel


class ScoutingModelTests(unittest.TestCase):
    def test_market_value_estimator_returns_expected_shape(self):
        estimator = MarketValueEstimator()
        prediction = estimator.predict({
            'position': 'CM',
            'age': 23,
            'minutes_played': 2250,
            'matches_played': 28,
            'goals': 7,
            'assists': 5,
            'total_xg': 6.4,
            'progressive_passes': 112,
            'key_passes': 34,
            'pass_accuracy': 84.2,
            'contract_years_remaining': 3.2,
        })

        self.assertGreater(prediction['estimateMillionEUR'], 15.0)
        self.assertEqual(prediction['band'], 'premium-starter')
        self.assertIn('EUR', prediction['displayValue'])
        self.assertGreaterEqual(prediction['confidence'], 70.0)
        self.assertEqual(prediction['predictionSource'], 'heuristic_fallback')
        self.assertIn('modelDeploymentSource', prediction)

    def test_market_value_estimator_trains_supervised_model(self):
        with TemporaryDirectory() as temp_dir:
            estimator = MarketValueEstimator(model_path=str(Path(temp_dir) / 'market_value.joblib'), min_samples=12)
            training_rows = []
            for index in range(18):
                age = 20 + (index % 7)
                minutes = 1400 + index * 75
                goals = 4 + (index % 6)
                assists = 2 + (index % 5)
                xg_total = 3.5 + index * 0.35
                progressive_passes = 55 + index * 6
                key_passes = 18 + index * 2
                market_value_million = (
                    5.0
                    + goals * 1.4
                    + assists * 1.1
                    + xg_total * 0.8
                    + progressive_passes * 0.03
                    + key_passes * 0.08
                    - max(0, age - 27) * 0.5
                )
                training_rows.append({
                    'position': 'CM' if index % 2 == 0 else 'FW',
                    'age': age,
                    'minutes_played': minutes,
                    'matches_played': 18 + index,
                    'goals': goals,
                    'assists': assists,
                    'total_xg': xg_total,
                    'progressive_passes': progressive_passes,
                    'key_passes': key_passes,
                    'pressures': 120 + index * 3,
                    'tackles': 22 + index,
                    'interceptions': 14 + index,
                    'pass_accuracy': 81.0 + (index % 5),
                    'contract_years_remaining': 2.0 + (index % 3),
                    'market_value_eur': market_value_million * 1_000_000,
                })

            training_result = estimator.train(training_rows)
            self.assertEqual(training_result['status'], 'success')
            self.assertTrue(estimator.is_fitted)

            prediction = estimator.predict({
                'position': 'CM',
                'age': 24,
                'minutes_played': 2500,
                'matches_played': 30,
                'goals': 8,
                'assists': 7,
                'total_xg': 6.2,
                'progressive_passes': 112,
                'key_passes': 32,
                'pressures': 155,
                'tackles': 28,
                'interceptions': 20,
                'pass_accuracy': 86.0,
                'contract_years_remaining': 3.0,
            })

            self.assertEqual(prediction['predictionSource'], 'trained_model')
            self.assertGreater(prediction['estimateMillionEUR'], 10.0)
            self.assertTrue(Path(training_result['artifact_path']).exists())
            self.assertIn('modelDeploymentSource', prediction)

    def test_vaep_action_model_rewards_successful_progression(self):
        model = VaepActionValueModel()
        successful = model.predict({
            'type_name': 'pass',
            'x': 42,
            'y': 48,
            'end_x': 78,
            'end_y': 44,
            'is_successful': True,
            'progressive_pass': True,
            'entered_final_third': True,
            'is_key_pass': True,
        })
        failed = model.predict({
            'type_name': 'pass',
            'x': 42,
            'y': 48,
            'end_x': 78,
            'end_y': 44,
            'is_successful': False,
            'progressive_pass': True,
            'entered_final_third': True,
            'is_key_pass': True,
        })

        self.assertGreater(successful['vaepValue'], failed['vaepValue'])
        self.assertGreater(successful['components']['offensiveValue'], 0.0)
        self.assertEqual(successful['predictionSource'], 'heuristic_fallback')
        self.assertIn('modelDeploymentSource', successful)

    def test_vaep_action_model_trains_supervised_model(self):
        with TemporaryDirectory() as temp_dir:
            model = VaepActionValueModel(model_path=str(Path(temp_dir) / 'vaep_action.joblib'), min_samples=16)
            training_rows = []
            for index in range(24):
                successful = index % 4 != 0
                progressive = index % 2 == 0
                entered_box = index % 5 == 0
                key_pass = index % 3 == 0
                is_goal = index % 11 == 0
                x = 35 + (index % 20)
                end_x = x + (22 if successful else 6)
                label = (
                    -0.08
                    + (0.18 if successful else -0.06)
                    + (0.12 if progressive else 0.0)
                    + (0.16 if entered_box else 0.0)
                    + (0.09 if key_pass else 0.0)
                    + (0.52 if is_goal else 0.0)
                )
                training_rows.append({
                    'type_name': 'pass',
                    'x': x,
                    'y': 48,
                    'end_x': end_x,
                    'end_y': 44,
                    'is_successful': successful,
                    'progressive_pass': progressive,
                    'entered_final_third': True,
                    'entered_box': entered_box,
                    'is_key_pass': key_pass,
                    'is_goal': is_goal,
                    'high_regain': index % 6 == 0,
                    'vaep_value': round(label, 4),
                })

            training_result = model.train(training_rows)
            self.assertEqual(training_result['status'], 'success')
            self.assertTrue(model.is_fitted)

            successful = model.predict({
                'type_name': 'pass',
                'x': 42,
                'y': 48,
                'end_x': 78,
                'end_y': 44,
                'is_successful': True,
                'progressive_pass': True,
                'entered_final_third': True,
                'entered_box': True,
                'is_key_pass': True,
            })
            failed = model.predict({
                'type_name': 'pass',
                'x': 42,
                'y': 48,
                'end_x': 58,
                'end_y': 44,
                'is_successful': False,
                'progressive_pass': False,
                'entered_final_third': True,
                'entered_box': False,
                'is_key_pass': False,
            })

            self.assertEqual(successful['predictionSource'], 'trained_model')
            self.assertGreater(successful['vaepValue'], failed['vaepValue'])
            self.assertIn('learnedAdjustment', successful['components'])
            self.assertIn('modelDeploymentSource', successful)

    def test_xg_feature_extraction_handles_contextual_fields(self):
        features = XGModel._extract_features({
            'location': {'x': 86, 'y': 43},
            'body_part': 'left_foot',
            'shot_type': 'open_play',
            'assist_type': 'cutback through ball',
            'under_pressure': True,
            'team_score': 1,
            'opponent_score': 1,
            'minute': 78,
            'qualifiers': {'102': '55', '103': '38'},
        })

        self.assertIsNotNone(features)
        self.assertEqual(len(features), 22)


if __name__ == '__main__':
    unittest.main()