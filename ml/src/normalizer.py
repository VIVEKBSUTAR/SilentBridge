import sys
import os
import numpy as np

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import FEATURES, HALL_SENSORS

class Normalizer:
    def __init__(self):
        # Find indices of hall sensors in the FEATURES list
        self.hall_indices = [FEATURES.index(sensor) for sensor in HALL_SENSORS]
        
    def normalize_hall_sensors(self, array_2d):
        """
        Normalizes the hall sensor columns (0 to 4095) to (0.0 to 1.0)
        array_2d shape: (N_frames, 13)
        Returns a normalized copy of the array.
        """
        normalized = array_2d.copy()
        
        for idx in self.hall_indices:
            # Min-max normalization assuming known absolute min/max for ADC
            normalized[:, idx] = np.clip(normalized[:, idx] / 4095.0, 0.0, 1.0)
            
        return normalized
