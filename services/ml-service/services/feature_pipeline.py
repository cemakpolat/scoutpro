import numpy as np
import logging

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
        except ValueError:
            return 0.0, 0.0
            
        if provider.lower() == "statsbomb":
            # StatsBomb: 120 x 80
            norm_x = x / 120.0
            norm_y = y / 80.0
        elif provider.lower() == "opta":
            # Opta: usually 100 x 100 percentages
            norm_x = x / 100.0
            norm_y = y / 100.0
        else:
            # Default fallback 105 x 68 meters
            norm_x = x / self.pitch_length
            norm_y = y / self.pitch_width
            
        return max(0.0, min(1.0, norm_x)), max(0.0, min(1.0, norm_y))
        
    def create_pass_success_tensor(self, event_data: dict) -> list:
        """
        Create a flat tensor array for Pass Success Probability prediction.
        Shape: [start_x, start_y, end_x, end_y, is_pressure, pass_length]
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
            
            # Simple euclidean distance approximation on normalized pitch
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

