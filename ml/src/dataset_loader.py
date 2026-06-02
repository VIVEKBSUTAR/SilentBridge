import os
import json
import glob
import sys

# Ensure config can be imported when running from src/ or ml/
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import RAW_DATA_DIR, FEATURES

class DatasetLoader:
    def __init__(self):
        self.raw_dir = RAW_DATA_DIR
        
    def get_labels(self):
        if not os.path.exists(self.raw_dir):
            return []
        labels = [d for d in os.listdir(self.raw_dir) if os.path.isdir(os.path.join(self.raw_dir, d))]
        return sorted(labels)
        
    def load_and_validate(self):
        labels = self.get_labels()
        valid_recordings = []
        
        for label in labels:
            label_dir = os.path.join(self.raw_dir, label)
            files = glob.glob(os.path.join(label_dir, "*.json"))
            
            for file_path in files:
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                except Exception as e:
                    print(f"Skipping {file_path}: Failed to read JSON - {e}")
                    continue
                    
                # Validate
                if not all(k in data for k in ("label", "frame_count", "frames")):
                    print(f"Skipping {file_path}: Missing root keys")
                    continue
                    
                if data["frame_count"] <= 0 or not data["frames"]:
                    print(f"Skipping {file_path}: Empty frames")
                    continue
                    
                # Validate frames
                valid_frames = True
                for frame in data["frames"]:
                    if not all(f in frame for f in FEATURES):
                        valid_frames = False
                        break
                        
                if not valid_frames:
                    print(f"Skipping {file_path}: Missing features in frames")
                    continue
                    
                valid_recordings.append(data)
                
        return valid_recordings
