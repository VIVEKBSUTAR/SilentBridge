import sys
import os
import numpy as np
from scipy.interpolate import interp1d

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import TARGET_FRAMES

class Resampler:
    @staticmethod
    def resample(sequence, target_len=TARGET_FRAMES):
        """
        Resamples a sequence of shape (original_len, feature_count) 
        to (target_len, feature_count) using linear interpolation.
        """
        original_len = sequence.shape[0]
        feature_count = sequence.shape[1]
        
        if original_len == target_len:
            return sequence
            
        # Create an original time array from 0 to 1
        x_old = np.linspace(0, 1, num=original_len)
        
        # Create a new time array from 0 to 1
        x_new = np.linspace(0, 1, num=target_len)
        
        # We need an array to hold the resampled features
        resampled_sequence = np.zeros((target_len, feature_count), dtype=np.float32)
        
        # Interpolate each feature column independently
        for i in range(feature_count):
            f = interp1d(x_old, sequence[:, i], kind='linear')
            resampled_sequence[:, i] = f(x_new)
            
        return resampled_sequence
