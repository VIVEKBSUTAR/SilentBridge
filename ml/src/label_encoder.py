import os
import json
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import PROCESSED_DATA_DIR

class DynamicLabelEncoder:
    def __init__(self, labels):
        self.labels = sorted(list(set(labels)))
        self.label_map = {label: idx for idx, label in enumerate(self.labels)}
        
    def encode(self, label):
        return self.label_map[label]
        
    def save_mapping(self):
        if not os.path.exists(PROCESSED_DATA_DIR):
            os.makedirs(PROCESSED_DATA_DIR)
            
        file_path = os.path.join(PROCESSED_DATA_DIR, "label_map.json")
        with open(file_path, "w") as f:
            json.dump(self.label_map, f, indent=2)
