import numpy as np
import logging
from collections import defaultdict, deque
import json

try:
    import torch
except ImportError:
    torch = None

logger = logging.getLogger(__name__)

class FeatureEngineeringPipeline:
    """
    Adapter to sanitize raw spatial coordinates (StatsBomb/Opta) 
    and parse them into standardized PyTorch/Scikit tensors.
    """
    
    def __init__(self, pitch_length=105.0, pitch_width=68.0):
        self.pitch_length = pitch_length
        self.pitch_width = pitch_width
        
    def sanitize_coordinates(self, x, y, provider="StatsBomb"):
        """
        Normalize coordinates to a 0-1 scale regardless of the data provider.
        """
        if x is None or y is None:
            return 0.0, 0.0
            
        try:
            x, y = float(x), float(y)
        except (ValueError, TypeError):
            return 0.0, 0.0
            
        if provider.lower() == "statsbomb":
            norm_x = x / 120.0
            norm_y = y / 80.0
        elif provider.lower() == "opta":
            norm_x = x / 100.0
            norm_y = y / 100.0
        else:
            norm_x = x / self.pitch_length
            norm_y = y / self.pitch_width
            
        return max(0.0, min(1.0, norm_x)), max(0.0, min(1.0, norm_y))
        
    def create_pass_success_tensor(self, event_data: dict) -> list:
        """
        Create a flat tensor array for Pass Success Probability prediction.
        """
        try:
            provider = event_data.get('provider', 'StatsBomb')
            start_x, start_y = self.sanitize_coordinates(
                event_data.get('x'), event_data.get('y'), provider
            )
            
            end_x, end_y = self.sanitize_coordinates(
                event_data.get('end_x'), event_data.get('end_y'), provider
            )
            
            is_pressure = 1.0 if event_data.get('under_pressure') else 0.0
            
            pass_length = np.sqrt((end_x - start_x)**2 + (end_y - start_y)**2)
            
            tensor_list = [start_x, start_y, end_x, end_y, is_pressure, pass_length]
            
            if torch:
                return torch.tensor(tensor_list, dtype=torch.float32)
            else:
                return np.array(tensor_list, dtype=np.float32)
                
        except Exception as e:
            logger.error(f"Error creating tensor: {e}")
            return None

    def process_event_to_features(self, event_data: dict):
        """
        Main entrypoint for an event. Parses it into ML features.
        """
        event_type = str(event_data.get('type')).lower()
        features = {}
        
        if 'pass' in event_type:
            features['pass_tensor'] = self.create_pass_success_tensor(event_data)
            
        return features

class TimeSeriesFeatureExtractor:
    """
    Extracts time-series features like rolling averages for player form.
    Maintains a rolling window of recent matches/events per player.
    """
    def __init__(self, window_size=5):
        self.window_size = window_size
        # player_id -> {"passes": deque, "shots": deque, "xg": deque}
        self.player_history = defaultdict(lambda: {
            "passes": deque(maxlen=window_size),
            "successful_passes": deque(maxlen=window_size),
            "shots": deque(maxlen=window_size),
            "xg": deque(maxlen=window_size)
        })
        
    def update_player_match_stats(self, player_id: str, match_stats: dict):
        """
        Update rolling history for a player with aggregated match stats.
        match_stats should contain: passes, successful_passes, shots, xg
        """
        history = self.player_history[player_id]
        
        history["passes"].append(match_stats.get("passes", 0))
        history["successful_passes"].append(match_stats.get("successful_passes", 0))
        history["shots"].append(match_stats.get("shots", 0))
        history["xg"].append(match_stats.get("xg", 0.0))
        
    def get_player_form_features(self, player_id: str) -> dict:
        """
        Calculate rolling averages and momentum for a player.
        """
        history = self.player_history[player_id]
        
        def _avg(d):
            return sum(d) / len(d) if len(d) > 0 else 0.0
            
        avg_passes = _avg(history["passes"])
        avg_succ_passes = _avg(history["successful_passes"])
        avg_shots = _avg(history["shots"])
        avg_xg = _avg(history["xg"])
        
        pass_accuracy = avg_succ_passes / avg_passes if avg_passes > 0 else 0.0
        
        # Simple momentum (last match vs average of previous)
        momentum_xg = 0.0
        if len(history["xg"]) > 1:
            recent_xg = history["xg"][-1]
            prev_xg_avg = sum(list(history["xg"])[:-1]) / (len(history["xg"]) - 1)
            momentum_xg = recent_xg - prev_xg_avg
            
        return {
            "rolling_passes": avg_passes,
            "rolling_pass_accuracy": pass_accuracy,
            "rolling_shots": avg_shots,
            "rolling_xg": avg_xg,
            "momentum_xg": momentum_xg,
            "matches_played": len(history["passes"])
        }
        
    def get_form_tensor(self, player_id: str):
        """
        Returns a tensor representation of the player's current form for model input.
        """
        features = self.get_player_form_features(player_id)
        tensor_list = [
            features["rolling_passes"],
            features["rolling_pass_accuracy"],
            features["rolling_shots"],
            features["rolling_xg"],
            features["momentum_xg"]
        ]
        
        if torch:
            return torch.tensor(tensor_list, dtype=torch.float32)
        else:
            return np.array(tensor_list, dtype=np.float32)

