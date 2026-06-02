import numpy as np
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import FEATURES

class FeatureExtractor:
    @staticmethod
    def extract(recording):
        """
        Converts the list of frame dictionaries into a (N, 13) NumPy array.
        Ignores timestamp.
        """
        frames = recording["frames"]
        extracted = []
        for frame in frames:
            row = [frame[feature] for feature in FEATURES]
            extracted.append(row)
        return np.array(extracted, dtype=np.float32)
