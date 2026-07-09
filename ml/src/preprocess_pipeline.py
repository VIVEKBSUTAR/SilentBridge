"""
SilentBridge — Updated Preprocessing Pipeline

Changes from v1:
  - Loads multi-user dataset (user_XXX/ folders) as well as legacy flat layout
  - Optionally applies per-user sensor calibration instead of global /4095
  - Writes user_id into preprocessing_metadata.json for LOSO splits
  - Everything else unchanged (StandardScaler on IMU, resample to 100f, etc.)

Run:
    python preprocess_pipeline.py                     # standard
    python preprocess_pipeline.py --use-user-calib    # per-user calibration
"""

import os
import sys
import json
import argparse
import datetime
import numpy as np
from sklearn.preprocessing import StandardScaler
import joblib

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import PROCESSED_DATA_DIR, SCALERS_DIR, TARGET_FRAMES, FEATURE_COUNT, FEATURES, MPU_FEATURES

from dataset_loader import DatasetLoader
from feature_extractor import FeatureExtractor
from normalizer import Normalizer, UserNormalizer
from resampler import Resampler
from label_encoder import DynamicLabelEncoder
from dataset_statistics import DatasetStatistics


def main(use_user_calib=False):
    print("Starting SilentBridge Preprocessing Pipeline (v2)…")

    loader   = DatasetLoader()
    is_multi = loader._is_multi_user()
    print(f"Dataset layout: {'multi-user' if is_multi else 'single-user (legacy)'}")

    recordings = loader.load_and_validate()
    if not recordings:
        print("No valid recordings found. Exiting.")
        sys.exit(1)
    print(f"Loaded {len(recordings)} recordings from "
          f"{len(set(r['user_id'] for r in recordings))} user(s).")

    # ── Per-user calibration normalizers (optional) ──────────────────────────
    user_normalizers = {}
    if use_user_calib:
        calib_dir = os.path.join(os.path.dirname(PROCESSED_DATA_DIR), "..", "data", "calibration")
        users_with_calib = 0
        for user_id in set(r["user_id"] for r in recordings):
            calib_path = os.path.join(calib_dir, f"{user_id}_calibration.json")
            un = UserNormalizer()
            if os.path.exists(calib_path):
                un.load_calibration(calib_path)
                user_normalizers[user_id] = un
                users_with_calib += 1
            else:
                print(f"  [WARN] No calibration file for {user_id}, using global /4095")
                user_normalizers[user_id] = Normalizer()  # fallback
        print(f"Per-user calibration: {users_with_calib}/{len(user_normalizers)} users have calib files.")
    else:
        global_norm = Normalizer()

    resampler = Resampler()

    # ── Feature extraction ───────────────────────────────────────────────────
    X_list, y_labels, metadata_list = [], [], []

    for rec in recordings:
        user_id = rec.get("user_id", "user_000")
        label   = rec["label"]
        sample_id = rec.get("sample_id", "UNKNOWN")

        # Extract (N, 13) matrix
        features_2d = FeatureExtractor.extract(rec)

        # Normalise Hall sensors
        if use_user_calib:
            norm = user_normalizers.get(user_id, Normalizer())
        else:
            norm = global_norm
        normed = norm.normalize_hall_sensors(features_2d)

        # Resample → (100, 13)
        resampled = resampler.resample(normed)

        X_list.append(resampled)
        y_labels.append(label)
        metadata_list.append({
            "sample_id":       sample_id,
            "label":           label,
            "user_id":         user_id,
            "original_frames": rec["frame_count"],
            "resampled_frames": TARGET_FRAMES,
            "norm_method":     "user_calibration" if use_user_calib else "global_4095",
        })

    X = np.stack(X_list)   # (N, 100, 13)

    # ── Label encoding ───────────────────────────────────────────────────────
    encoder = DynamicLabelEncoder(y_labels)
    encoder.save_mapping()
    y = np.array([encoder.encode(l) for l in y_labels], dtype=np.int32)

    # ── IMU standardisation ──────────────────────────────────────────────────
    print("Standardising IMU features…")
    mpu_indices = [FEATURES.index(f) for f in MPU_FEATURES]
    N = X.shape[0]
    X_2d = X.reshape(-1, FEATURE_COUNT)
    mpu_data = X_2d[:, mpu_indices]

    scaler = StandardScaler()
    X_2d[:, mpu_indices] = scaler.fit_transform(mpu_data)
    X = X_2d.reshape(N, TARGET_FRAMES, FEATURE_COUNT)

    # ── Save artefacts ───────────────────────────────────────────────────────
    os.makedirs(SCALERS_DIR, exist_ok=True)
    joblib.dump(scaler, os.path.join(SCALERS_DIR, "feature_scaler.pkl"))

    os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)
    np.save(os.path.join(PROCESSED_DATA_DIR, "X.npy"), X)
    np.save(os.path.join(PROCESSED_DATA_DIR, "y.npy"), y)

    # ── Export scaler params as JSON for Android ─────────────────────────────
    scaler_json_path = os.path.join(SCALERS_DIR, "scaler_params.json")
    with open(scaler_json_path, "w") as f:
        json.dump({
            "mean":  scaler.mean_.tolist(),
            "scale": scaler.scale_.tolist(),
            "feature_names": MPU_FEATURES,
        }, f, indent=2)
    print(f"Scaler params (for Android) saved to {scaler_json_path}")

    # ── Preprocessing metadata ───────────────────────────────────────────────
    meta = {
        "dataset_version":     "v2",
        "target_frames":       TARGET_FRAMES,
        "feature_count":       FEATURE_COUNT,
        "created_at":          datetime.datetime.now().isoformat(),
        "normalization_method": "user_calibration" if use_user_calib else "global_4095",
        "scaler_type":         "StandardScaler",
        "multi_user":          is_multi,
        "num_users":           len(set(r["user_id"] for r in recordings)),
        "recordings":          metadata_list,
    }
    with open(os.path.join(PROCESSED_DATA_DIR, "preprocessing_metadata.json"), "w") as f:
        json.dump(meta, f, indent=2)

    # ── Statistics ───────────────────────────────────────────────────────────
    stats = DatasetStatistics.generate_and_save(metadata_list, X.shape, y.shape)
    DatasetStatistics.print_stats(stats)

    print(f"\nPreprocessing complete. Artefacts in {PROCESSED_DATA_DIR}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--use-user-calib", action="store_true",
                   help="Apply per-user min/max calibration instead of global /4095")
    args = p.parse_args()
    main(use_user_calib=args.use_user_calib)