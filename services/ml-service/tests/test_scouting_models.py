import unittest

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