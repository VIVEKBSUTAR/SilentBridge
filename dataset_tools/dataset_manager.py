import os
import json
import glob
from datetime import datetime
from config import DATASET_PATH

def create_label_directory(label):
    """Ensure the directory for the given label exists."""
    label_path = os.path.join(DATASET_PATH, label)
    if not os.path.exists(label_path):
        os.makedirs(label_path)
    return label_path

def count_existing_samples(label):
    """Count how many recordings already exist for a given label."""
    label_path = os.path.join(DATASET_PATH, label)
    if not os.path.exists(label_path):
        return 0
    return len(glob.glob(os.path.join(label_path, f"{label}_*.json")))

def get_next_sample_id(label):
    """Generate the next available sample ID (e.g. HELLO_0001)."""
    label_path = os.path.join(DATASET_PATH, label)
    if not os.path.exists(label_path):
        return f"{label}_0001"
        
    files = glob.glob(os.path.join(label_path, f"{label}_*.json"))
    max_num = 0
    for f in files:
        basename = os.path.basename(f)
        try:
            num_str = basename.replace(f"{label}_", "").replace(".json", "")
            num = int(num_str)
            if num > max_num:
                max_num = num
        except ValueError:
            pass
            
    next_num = max_num + 1
    return f"{label}_{next_num:04d}"

def validate_recording(frames):
    """Ensure the recorded frames are valid."""
    if not frames:
        return False
    
    required_keys = {
        "timestamp", "thumb", "index", "middle", "ring", "little",
        "ax", "ay", "az", "gx", "gy", "gz", "pitch", "roll"
    }
    
    for frame in frames:
        if not required_keys.issubset(frame.keys()):
            return False
            
    return True

def save_recording(label, frames):
    """Save the recording to a JSON file as per the schema."""
    if not validate_recording(frames):
        raise ValueError("Invalid recording frames. Missing required features.")
        
    create_label_directory(label)
    sample_id = get_next_sample_id(label)
    
    recording = {
        "label": label,
        "sample_id": sample_id,
        "recorded_at": datetime.now().isoformat(),
        "frame_count": len(frames),
        "frames": frames
    }
    
    file_path = os.path.join(DATASET_PATH, label, f"{sample_id}.json")
    with open(file_path, "w") as f:
        json.dump(recording, f, indent=2)
        
    return file_path
