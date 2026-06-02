import os
import sys
import json
import numpy as np
import matplotlib.pyplot as plt

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import PROCESSED_DATA_DIR, BASE_DIR, FEATURES, HALL_SENSORS, MPU_FEATURES

def main():
    print("Starting Dataset Validation...")
    
    x_path = os.path.join(PROCESSED_DATA_DIR, "X.npy")
    y_path = os.path.join(PROCESSED_DATA_DIR, "y.npy")
    meta_path = os.path.join(PROCESSED_DATA_DIR, "preprocessing_metadata.json")
    label_map_path = os.path.join(PROCESSED_DATA_DIR, "label_map.json")
    plots_dir = os.path.join(BASE_DIR, "ml", "data", "plots")
    
    if not os.path.exists(plots_dir):
        os.makedirs(plots_dir)
        
    X = np.load(x_path)
    y = np.load(y_path)
    
    with open(meta_path, "r") as f:
        metadata = json.load(f)
        
    with open(label_map_path, "r") as f:
        label_map = json.load(f)
        
    reverse_label_map = {v: k for k, v in label_map.items()}
    
    # 2. Print basics
    print(f"X shape: {X.shape}")
    print(f"y shape: {y.shape}")
    
    unique_labels, counts = np.unique(y, return_counts=True)
    print(f"Unique labels: {unique_labels}")
    for lbl, count in zip(unique_labels, counts):
        print(f"  {reverse_label_map[lbl]} (ID: {lbl}): {count}")
        
    # 3. Verify values
    has_nan = np.isnan(X).any()
    has_inf = np.isinf(X).any()
    print(f"Contains NaN: {has_nan}")
    print(f"Contains Inf: {has_inf}")
    
    hall_indices = [FEATURES.index(f) for f in HALL_SENSORS]
    mpu_indices = [FEATURES.index(f) for f in MPU_FEATURES]
    
    X_2d = X.reshape(-1, len(FEATURES))
    hall_data = X_2d[:, hall_indices]
    mpu_data = X_2d[:, mpu_indices]
    
    hall_min, hall_max = np.min(hall_data), np.max(hall_data)
    print(f"Hall sensor range: [{hall_min:.4f}, {hall_max:.4f}]")
    
    mpu_mean = np.mean(mpu_data, axis=0)
    mpu_var = np.var(mpu_data, axis=0)
    overall_mpu_mean = np.mean(mpu_mean)
    overall_mpu_var = np.mean(mpu_var)
    print(f"MPU standardized overall mean: {overall_mpu_mean:.6f}")
    print(f"MPU standardized overall variance: {overall_mpu_var:.6f}")
    
    # 4. Generate JSON report
    report = {
        "x_shape": list(X.shape),
        "y_shape": list(y.shape),
        "label_counts": {reverse_label_map[lbl]: int(c) for lbl, c in zip(unique_labels, counts)},
        "has_nan": bool(has_nan),
        "has_inf": bool(has_inf),
        "hall_sensor_min": float(hall_min),
        "hall_sensor_max": float(hall_max),
        "mpu_means": [float(m) for m in mpu_mean],
        "mpu_variances": [float(v) for v in mpu_var],
        "mpu_overall_mean": float(overall_mpu_mean),
        "mpu_overall_variance": float(overall_mpu_var)
    }
    
    with open(os.path.join(PROCESSED_DATA_DIR, "validation_report.json"), "w") as f:
        json.dump(report, f, indent=2)
        
    # 5. Create plots
    print("Generating plots...")
    
    # Plot A: Feature distributions
    fig, axes = plt.subplots(3, 5, figsize=(20, 12))
    axes = axes.flatten()
    for i, feature in enumerate(FEATURES):
        axes[i].hist(X_2d[:, i], bins=50, alpha=0.7)
        axes[i].set_title(f"{feature} Distribution")
    
    # Remove empty subplots
    for j in range(len(FEATURES), len(axes)):
        fig.delaxes(axes[j])
        
    plt.tight_layout()
    plt.savefig(os.path.join(plots_dir, "feature_distributions.png"))
    plt.close()
    
    # Plot B: Frame length distribution
    original_frames = [rec["original_frames"] for rec in metadata["recordings"]]
    plt.figure(figsize=(10, 6))
    plt.hist(original_frames, bins=20, alpha=0.7, color='orange')
    plt.title("Original Frame Length Distribution")
    plt.xlabel("Frame Count")
    plt.ylabel("Frequency")
    plt.tight_layout()
    plt.savefig(os.path.join(plots_dir, "frame_lengths.png"))
    plt.close()
    
    # Plot C: Sample gesture traces (first recording)
    sample_X = X[0] # (100, 13)
    fig, axes = plt.subplots(3, 1, figsize=(12, 10))
    
    # Hall traces
    for i in hall_indices:
        axes[0].plot(sample_X[:, i], label=FEATURES[i])
    axes[0].set_title(f"Sample Trace - Hall Sensors ({reverse_label_map[y[0]]})")
    axes[0].legend()
    
    # Accel traces
    accel_indices = [FEATURES.index(f) for f in ["ax", "ay", "az"]]
    for i in accel_indices:
        axes[1].plot(sample_X[:, i], label=FEATURES[i])
    axes[1].set_title("Sample Trace - Accelerometer (Standardized)")
    axes[1].legend()
    
    # Gyro & Orientation traces
    rest_indices = [FEATURES.index(f) for f in ["gx", "gy", "gz", "pitch", "roll"]]
    for i in rest_indices:
        axes[2].plot(sample_X[:, i], label=FEATURES[i])
    axes[2].set_title("Sample Trace - Gyroscope & Orientation (Standardized)")
    axes[2].legend()
    
    plt.tight_layout()
    plt.savefig(os.path.join(plots_dir, "sample_traces.png"))
    plt.close()
    
    print("Validation complete. Artifacts saved in ml/data/plots and ml/data/processed.")

if __name__ == "__main__":
    main()
