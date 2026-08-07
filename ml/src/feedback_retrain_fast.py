"""
SilentBridge — Fast Feedback Retraining

Instead of reprocessing all 484 original JSONs every time,
this script:
  1. Loads existing X.npy and y.npy directly (already preprocessed)
  2. Processes ONLY the new phone_feedback JSONs
  3. Appends them to the existing arrays
  4. Retrains on the combined result

This makes preprocessing near-instant (seconds vs minutes).

Usage:
    python ml/src/feedback_retrain_fast.py --log feedback_log.jsonl
    python ml/src/feedback_retrain_fast.py --log feedback_log.jsonl --dry-run
    python ml/src/feedback_retrain_fast.py --log feedback_log.jsonl --no-train
"""

import os
import sys
import json
import argparse
import subprocess
from datetime import datetime
import numpy as np

# ── Paths ────────────────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR   = os.path.dirname(os.path.dirname(SCRIPT_DIR))   # SilentBridge/
ML_DIR     = os.path.join(BASE_DIR, "ml")
RAW_DIR    = os.path.join(BASE_DIR, "data", "raw")
REVIEW_DIR = os.path.join(BASE_DIR, "data", "review")
PROCESSED_DIR = os.path.join(ML_DIR, "data", "processed")
SCALERS_DIR   = os.path.join(ML_DIR, "data", "scalers")
MODELS_DIR    = os.path.join(ML_DIR, "models")

sys.path.append(ML_DIR)
sys.path.append(os.path.join(ML_DIR, "src"))

from config import FEATURES, HALL_SENSORS, MPU_FEATURES, TARGET_FRAMES, FEATURE_COUNT
from feature_extractor import FeatureExtractor
from normalizer import Normalizer
from resampler import Resampler

SUPPORTED_LABELS = [
    "HELLO", "HELP", "WATER", "FOOD", "YES", "NO", "THANK_YOU", "MEDICINE"
]
REQUIRED_KEYS = {
    "timestamp", "thumb", "index", "middle", "ring", "little",
    "ax", "ay", "az", "gx", "gy", "gz", "pitch", "roll"
}


# ── Load existing preprocessed data ─────────────────────────────────────────
def load_existing_arrays():
    X_path      = os.path.join(PROCESSED_DIR, "X.npy")
    y_path      = os.path.join(PROCESSED_DIR, "y.npy")
    label_path  = os.path.join(PROCESSED_DIR, "label_map.json")

    if not os.path.exists(X_path) or not os.path.exists(y_path):
        print("[ERROR] X.npy / y.npy not found in ml/data/processed/")
        print("        Run preprocess_pipeline.py once first to generate them.")
        sys.exit(1)

    X = np.load(X_path)
    y = np.load(y_path)

    with open(label_path) as f:
        label_map = json.load(f)   # {"HELLO": 1, "FOOD": 0, ...}

    print(f"Existing dataset: {X.shape[0]} samples, {len(label_map)} classes")
    return X, y, label_map


# ── Load scaler ───────────────────────────────────────────────────────────────
def load_scaler():
    import joblib
    scaler_path = os.path.join(SCALERS_DIR, "feature_scaler.pkl")
    if not os.path.exists(scaler_path):
        print("[ERROR] feature_scaler.pkl not found. Run preprocess_pipeline.py first.")
        sys.exit(1)
    return joblib.load(scaler_path)


# ── Preprocess a single recording dict → (100, 13) ──────────────────────────
def preprocess_one(recording: dict, scaler) -> np.ndarray:
    """
    Applies the exact same preprocessing pipeline as preprocess_pipeline.py
    but for a single recording.
    """
    mpu_indices = [FEATURES.index(f) for f in MPU_FEATURES]

    normalizer = Normalizer()
    resampler  = Resampler()

    # 1. Extract (N, 13)
    raw = FeatureExtractor.extract(recording)

    # 2. Normalise Hall sensors (/4095)
    normed = normalizer.normalize_hall_sensors(raw)

    # 3. Resample → (100, 13)
    resampled = resampler.resample(normed)

    # 4. Standardise IMU columns using the EXISTING scaler (do NOT refit)
    result = resampled.copy()
    result[:, mpu_indices] = scaler.transform(resampled[:, mpu_indices])

    return result.astype(np.float32)


# ── Feedback log ingestion ────────────────────────────────────────────────────
def load_log(log_path: str) -> list:
    entries = []
    with open(log_path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"  [WARN] Line {i}: invalid JSON — {e}")
    print(f"Loaded {len(entries)} entries from log.")
    return entries


def validate_frames(frames: list) -> bool:
    if not frames or len(frames) < 15:
        return False
    return all(REQUIRED_KEYS.issubset(f.keys()) for f in frames)


def save_for_review(entry: dict, dry_run: bool) -> str:
    predicted = entry.get("predicted", "UNKNOWN")
    ts        = entry.get("timestamp", datetime.now().isoformat()).replace(":", "-")
    filename  = f"REVIEW_{predicted}_{ts}.json"
    path      = os.path.join(REVIEW_DIR, filename)
    if not dry_run:
        os.makedirs(REVIEW_DIR, exist_ok=True)
        entry["true_label"]   = None
        entry["instructions"] = (
            "Set true_label to the correct gesture, "
            "then move to data/raw/<TRUE_LABEL>/<TRUE_LABEL>_XXXX.json"
        )
        with open(path, "w") as f:
            json.dump(entry, f, indent=2)
    return path


# ── Summary ───────────────────────────────────────────────────────────────────
def print_summary(entries):
    from collections import Counter
    yes = [e for e in entries if e.get("confirmed") is True]
    no  = [e for e in entries if e.get("confirmed") is False]
    yc  = Counter(e["predicted"] for e in yes)
    nc  = Counter(e["predicted"] for e in no)
    all_labels = sorted(set(list(yc) + list(nc)))

    print(f"\n{'='*48}")
    print(f"  Total: {len(entries)}   Yes: {len(yes)}   No: {len(no)}")
    print(f"  {'Gesture':<14} {'Yes':>5} {'No':>5}  {'Accuracy':>9}")
    print(f"  {'-'*40}")
    for lbl in all_labels:
        y, n = yc.get(lbl, 0), nc.get(lbl, 0)
        acc = f"{100*y/(y+n):.0f}%" if (y + n) > 0 else "—"
        print(f"  {lbl:<14} {y:>5} {n:>5}  {acc:>9}")
    print(f"{'='*48}\n")


# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    p = argparse.ArgumentParser(description="SilentBridge Fast Feedback Retraining")
    p.add_argument("--log",      required=True, help="Path to feedback_log.jsonl")
    p.add_argument("--dry-run",  action="store_true", help="Preview without writing")
    p.add_argument("--no-train", action="store_true", help="Ingest only, skip retraining")
    args = p.parse_args()

    print(f"\nSilentBridge Fast Feedback Retraining")
    print(f"  Log: {args.log}  |  Dry run: {args.dry_run}\n")

    # 1. Load existing preprocessed arrays
    X_existing, y_existing, label_map = load_existing_arrays()
    scaler = load_scaler()
    reverse_map = {v: k for k, v in label_map.items()}

    # 2. Load feedback log
    if not os.path.exists(args.log):
        print(f"[ERROR] Log file not found: {args.log}")
        sys.exit(1)

    entries = load_log(args.log)
    print_summary(entries)

    # 3. Process only YES entries → new (N, 100, 13) array
    new_X = []
    new_y = []
    review_count = 0
    skipped      = 0

    for entry in entries:
        predicted = entry.get("predicted", "")
        frames    = entry.get("frames", [])
        confirmed = entry.get("confirmed")

        if confirmed is True:
            if predicted not in SUPPORTED_LABELS:
                print(f"  [SKIP] Unknown label: {predicted}")
                skipped += 1
                continue

            if not validate_frames(frames):
                print(f"  [SKIP] {predicted}: invalid frames ({len(frames)} frames)")
                skipped += 1
                continue

            # Confidence sanity check — warn on very low confidence Yes taps
            conf = entry.get("confidence", 1.0)
            if conf < 0.5:
                print(f"  [WARN] {predicted}: conf={conf:.2f} is very low for a Yes — including anyway")

            # Preprocess
            recording = {"label": predicted, "frames": frames}
            try:
                X_sample = preprocess_one(recording, scaler)   # (100, 13)
                new_X.append(X_sample)
                new_y.append(label_map[predicted])
                tag = "[DRY RUN]" if args.dry_run else "ADDED"
                print(f"  [{tag}] {predicted:<14} conf={conf:.2f}  frames={len(frames)}")
            except Exception as e:
                print(f"  [ERROR] {predicted}: preprocessing failed — {e}")
                skipped += 1

        elif confirmed is False:
            path = save_for_review(entry, args.dry_run)
            conf = entry.get("confidence", 0)
            print(f"  [REVIEW] {predicted:<12} conf={conf:.2f}  → {os.path.basename(path)}")
            review_count += 1

    # 4. Append to existing arrays
    if not new_X:
        print("\nNo new valid confirmed samples to add. Exiting.")
        return

    new_X = np.stack(new_X)                          # (M, 100, 13)
    new_y = np.array(new_y, dtype=np.int32)          # (M,)

    X_combined = np.concatenate([X_existing, new_X], axis=0)
    y_combined = np.concatenate([y_existing, new_y], axis=0)

    print(f"\n── Dataset ──")
    print(f"  Before:  {X_existing.shape[0]} samples")
    print(f"  New:     {len(new_X)} samples")
    print(f"  After:   {X_combined.shape[0]} samples")

    # Class distribution after merge
    from collections import Counter
    dist = Counter(reverse_map.get(int(yi), str(yi)) for yi in y_combined)
    print(f"\n  Class distribution:")
    for lbl in sorted(dist):
        print(f"    {lbl:<14} {dist[lbl]:>4} samples")

    if not args.dry_run:
        np.save(os.path.join(PROCESSED_DIR, "X.npy"), X_combined)
        np.save(os.path.join(PROCESSED_DIR, "y.npy"), y_combined)
        print(f"\n  Saved updated X.npy and y.npy to {PROCESSED_DIR}")
    else:
        print(f"\n  [DRY RUN] Would save X.npy ({X_combined.shape}) and y.npy ({y_combined.shape})")

    print(f"  Saved for review: {review_count}  (in data/review/)")
    print(f"  Skipped:          {skipped}")

    # 5. Retrain
    if args.no_train:
        print("\nSkipping retraining (--no-train).")
        print("Run manually when ready:")
        print("  python ml/src/train.py --arch cnn --quantize")
        return

    if args.dry_run:
        print("\n[DRY RUN] Would run: python ml/src/train.py --arch cnn --quantize")
        return

    print("\n── Retraining ──")
    train_script = os.path.join(ML_DIR, "src", "train.py")
    result = subprocess.run(
        [sys.executable, train_script, "--arch", "cnn", "--quantize"],
        cwd=BASE_DIR
    )
    if result.returncode != 0:
        print("[ERROR] Training failed.")
        sys.exit(1)

    # 6. Deploy instructions
    tflite_files = []
    if os.path.exists(MODELS_DIR):
        for fname in os.listdir(MODELS_DIR):
            if fname.endswith(".tflite"):
                full = os.path.join(MODELS_DIR, fname)
                tflite_files.append((os.path.getmtime(full), full))

    if tflite_files:
        latest = sorted(tflite_files, reverse=True)[0][1]
        size_kb = os.path.getsize(latest) / 1024
        print(f"\n── New model ready ──")
        print(f"  {latest}  ({size_kb:.1f} KB)")
        print(f"\n  Push to phone:")
        print(f'  adb push "{latest}" /sdcard/Android/data/com.example.gloves/files/new_model.tflite')
        print(f"\n  Copy into app assets and rebuild in Android Studio to deploy.")


if __name__ == "__main__":
    main()