import os
import sys
import json
import numpy as np
import datetime
from sklearn.preprocessing import StandardScaler
import joblib

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import PROCESSED_DATA_DIR, SCALERS_DIR, TARGET_FRAMES, FEATURE_COUNT, FEATURES, MPU_FEATURES

from dataset_loader import DatasetLoader
from feature_extractor import FeatureExtractor
from normalizer import Normalizer
from resampler import Resampler
from label_encoder import DynamicLabelEncoder
from statistics import DatasetStatistics

def main():
    print("Starting Phase 2A Preprocessing Pipeline...")
    
    # 1. Load Data
    loader = DatasetLoader()
    recordings = loader.load_and_validate()
    
    if not recordings:
        print("No valid recordings found! Exiting.")
        sys.exit(1)
        
    print(f"Loaded {len(recordings)} valid recordings.")
    
    # Initialize Processors
    normalizer = Normalizer()
    resampler = Resampler()
    
    # Lists to hold processed data
    X_list = []
    y_labels = []
    metadata_list = []
    
    # 2. Extract, Normalize, Resample
    for rec in recordings:
        label = rec["label"]
        sample_id = rec.get("sample_id", "UNKNOWN")
        original_frames = rec["frame_count"]
        
        # Extract features (N, 13)
        features_2d = FeatureExtractor.extract(rec)
        
        # Normalize Hall sensors (in-place modification of a copy)
        norm_features = normalizer.normalize_hall_sensors(features_2d)
        
        # Resample to exactly TARGET_FRAMES (100)
        resampled_features = resampler.resample(norm_features)
        
        X_list.append(resampled_features)
        y_labels.append(label)
        
        metadata_list.append({
            "sample_id": sample_id,
            "label": label,
            "original_frames": original_frames,
            "resampled_frames": TARGET_FRAMES
        })
        
    # Convert X to 3D tensor
    X = np.stack(X_list) # Shape: (N, 100, 13)
    
    # 3. Label Encoding
    encoder = DynamicLabelEncoder(y_labels)
    encoder.save_mapping()
    y = np.array([encoder.encode(lbl) for lbl in y_labels], dtype=np.int32)
    
    # 4. Standardize MPU Features
    print("Standardizing MPU features...")
    # Find indices for MPU features
    mpu_indices = [FEATURES.index(f) for f in MPU_FEATURES]
    
    # Reshape X to 2D for scaling: (N * 100, 13)
    N = X.shape[0]
    X_2d = X.reshape(-1, FEATURE_COUNT)
    
    # Extract only MPU columns
    mpu_data = X_2d[:, mpu_indices]
    
    # Fit and transform
    scaler = StandardScaler()
    mpu_scaled = scaler.fit_transform(mpu_data)
    
    # Place scaled data back into X_2d
    X_2d[:, mpu_indices] = mpu_scaled
    
    # Reshape back to 3D: (N, 100, 13)
    X = X_2d.reshape(N, TARGET_FRAMES, FEATURE_COUNT)
    
    # Save Scaler
    if not os.path.exists(SCALERS_DIR):
        os.makedirs(SCALERS_DIR)
    joblib.dump(scaler, os.path.join(SCALERS_DIR, "feature_scaler.pkl"))
    
    # 5. Save Processed Data
    if not os.path.exists(PROCESSED_DATA_DIR):
        os.makedirs(PROCESSED_DATA_DIR)
        
    np.save(os.path.join(PROCESSED_DATA_DIR, "X.npy"), X)
    np.save(os.path.join(PROCESSED_DATA_DIR, "y.npy"), y)
    
    # Save Preprocessing Metadata
    meta_dict = {
        "dataset_version": "v1",
        "target_frames": TARGET_FRAMES,
        "feature_count": FEATURE_COUNT,
        "created_at": datetime.datetime.now().isoformat(),
        "normalization_method": "Hall/4095",
        "scaler_type": "StandardScaler",
        "recordings": metadata_list
    }
    with open(os.path.join(PROCESSED_DATA_DIR, "preprocessing_metadata.json"), "w") as f:
        json.dump(meta_dict, f, indent=2)
        
    # 6. Generate and Print Statistics
    stats = DatasetStatistics.generate_and_save(metadata_list, X.shape, y.shape)
    DatasetStatistics.print_stats(stats)
    
    print(f"\nPipeline completed successfully!")
    print(f"Artifacts saved in {PROCESSED_DATA_DIR}")

if __name__ == "__main__":
    main()
