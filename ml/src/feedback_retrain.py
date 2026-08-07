"""
SilentBridge — Feedback Ingestion & Retraining Script

Usage:
    python feedback_retrain.py --log feedback_log.jsonl
    python feedback_retrain.py --log feedback_log.jsonl --dry-run    # preview only
    python feedback_retrain.py --log feedback_log.jsonl --user user_phone

What it does:
    1. Reads feedback_log.jsonl produced by the Android app
    2. Confirmed (Yes) entries  → saved as new training samples in data/raw/
    3. Unconfirmed (No) entries → saved to data/review/ for manual relabelling
    4. Runs preprocess_pipeline.py on the expanded dataset
    5. Runs train.py with augmentation
    6. Converts the new model to TFLite
    7. Prints the adb push command to deploy it to the phone

Retrieve the log first:
    adb pull /sdcard/Android/data/com.example.gloves/files/feedback_log.jsonl ./feedback_log.jsonl
"""

import os
import sys
import json
import argparse
import subprocess
from datetime import datetime

# ── Path setup ──────────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR   = os.path.dirname(os.path.dirname(SCRIPT_DIR))    # SilentBridge/
RAW_DIR    = os.path.join(BASE_DIR, "data", "raw")
REVIEW_DIR = os.path.join(BASE_DIR, "data", "review")
MODELS_DIR = os.path.join(BASE_DIR, "ml", "models")

SUPPORTED_LABELS = [
    "HELLO", "HELP", "WATER", "FOOD", "YES", "NO", "THANK_YOU", "MEDICINE"
]

# ── Required frame keys (must match dataset spec) ────────────────────────────
REQUIRED_KEYS = {
    "timestamp", "thumb", "index", "middle", "ring", "little",
    "ax", "ay", "az", "gx", "gy", "gz", "pitch", "roll"
}


# ── Helpers ──────────────────────────────────────────────────────────────────
def load_log(log_path: str) -> list:
    entries = []
    skipped = 0
    with open(log_path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                entries.append(entry)
            except json.JSONDecodeError as e:
                print(f"  [WARN] Line {i}: invalid JSON — {e}")
                skipped += 1
    print(f"Loaded {len(entries)} entries ({skipped} skipped).")
    return entries


def validate_frames(frames: list) -> bool:
    if not frames or len(frames) < 15:
        return False
    for frame in frames:
        if not REQUIRED_KEYS.issubset(frame.keys()):
            return False
    return True


def get_next_sample_id(label: str, user_id: str = None) -> str:
    import glob
    if user_id:
        label_dir = os.path.join(RAW_DIR, user_id, label)
    else:
        label_dir = os.path.join(RAW_DIR, label)

    if not os.path.exists(label_dir):
        return f"{label}_0001"

    files = glob.glob(os.path.join(label_dir, f"{label}_*.json"))
    max_num = 0
    for fp in files:
        try:
            num = int(os.path.basename(fp).replace(f"{label}_", "").replace(".json", ""))
            max_num = max(max_num, num)
        except ValueError:
            pass
    return f"{label}_{max_num + 1:04d}"


def save_confirmed(entry: dict, user_id: str, dry_run: bool) -> str:
    """Save a Yes-confirmed entry as a new training sample."""
    label  = entry["predicted"]
    frames = entry["frames"]

    if label not in SUPPORTED_LABELS:
        return f"SKIP (unsupported label: {label})"

    if not validate_frames(frames):
        return f"SKIP (invalid frames: {len(frames)} frames)"

    sample_id = get_next_sample_id(label, user_id)

    if user_id:
        label_dir = os.path.join(RAW_DIR, user_id, label)
    else:
        label_dir = os.path.join(RAW_DIR, label)

    file_path = os.path.join(label_dir, f"{sample_id}.json")

    recording = {
        "label":       label,
        "sample_id":   sample_id,
        "user_id":     user_id or "phone_feedback",
        "source":      "rl_feedback",
        "recorded_at": entry.get("timestamp", datetime.now().isoformat()),
        "frame_count": len(frames),
        "frames":      frames,
    }

    if not dry_run:
        os.makedirs(label_dir, exist_ok=True)
        with open(file_path, "w") as f:
            json.dump(recording, f, indent=2)

    return f"SAVED → {file_path}" if not dry_run else f"[DRY RUN] would save → {file_path}"


def save_for_review(entry: dict, dry_run: bool) -> str:
    """Save a No-flagged entry to data/review/ for manual relabelling."""
    predicted = entry.get("predicted", "UNKNOWN")
    ts        = entry.get("timestamp", datetime.now().isoformat()).replace(":", "-")
    filename  = f"REVIEW_{predicted}_{ts}.json"
    file_path = os.path.join(REVIEW_DIR, filename)

    review_entry = {
        "predicted":   predicted,
        "confidence":  entry.get("confidence"),
        "confirmed":   False,
        "true_label":  None,     # to be filled in manually
        "recorded_at": entry.get("timestamp"),
        "frame_count": len(entry.get("frames", [])),
        "frames":      entry.get("frames", []),
        "instructions": (
            "Set true_label to the correct gesture name, "
            "then move this file to data/raw/<true_label>/<TRUE_LABEL>_XXXX.json"
        ),
    }

    if not dry_run:
        os.makedirs(REVIEW_DIR, exist_ok=True)
        with open(file_path, "w") as f:
            json.dump(review_entry, f, indent=2)

    return f"REVIEW → {file_path}" if not dry_run else f"[DRY RUN] would save → {file_path}"


# ── Summary printer ───────────────────────────────────────────────────────────
def print_summary(entries: list):
    from collections import Counter
    confirmed   = [e for e in entries if e.get("confirmed") is True]
    unconfirmed = [e for e in entries if e.get("confirmed") is False]

    print(f"\n{'='*50}")
    print(f"  Total entries:   {len(entries)}")
    print(f"  Confirmed (Yes): {len(confirmed)}")
    print(f"  Wrong (No):      {len(unconfirmed)}")
    print()

    yes_counts = Counter(e["predicted"] for e in confirmed)
    no_counts  = Counter(e["predicted"] for e in unconfirmed)
    all_labels = sorted(set(list(yes_counts.keys()) + list(no_counts.keys())))

    print(f"  {'Gesture':<15} {'Yes':>6} {'No':>6}  {'Accuracy':>10}")
    print(f"  {'-'*42}")
    for lbl in all_labels:
        y = yes_counts.get(lbl, 0)
        n = no_counts.get(lbl, 0)
        total = y + n
        acc = f"{100*y/total:.0f}%" if total > 0 else "—"
        print(f"  {lbl:<15} {y:>6} {n:>6}  {acc:>10}")
    print(f"{'='*50}\n")


# ── Retraining ────────────────────────────────────────────────────────────────
def run_retraining(dry_run: bool):
    ml_src = os.path.join(BASE_DIR, "ml", "src")

    steps = [
        {
            "name": "Preprocess",
            "cmd":  [sys.executable, os.path.join(ml_src, "preprocess_pipeline.py")],
        },
        {
            "name": "Train (CNN+BiLSTM+Attention, augmented, quantized)",
            "cmd":  [
                sys.executable, os.path.join(ml_src, "train.py"),
                "--arch", "cnn",
                "--augment",
                "--quantize",
            ],
        },
    ]

    for step in steps:
        print(f"\n── {step['name']} ──")
        if dry_run:
            print(f"  [DRY RUN] would run: {' '.join(step['cmd'])}")
            continue
        result = subprocess.run(step["cmd"], cwd=BASE_DIR)
        if result.returncode != 0:
            print(f"  [ERROR] Step failed with return code {result.returncode}")
            sys.exit(1)
        print(f"  ✓ Done.")


def find_tflite(dry_run: bool) -> str | None:
    if dry_run:
        return os.path.join(MODELS_DIR, "silentbridge_standard.tflite")
    candidates = []
    for fname in os.listdir(MODELS_DIR):
        if fname.endswith(".tflite"):
            full = os.path.join(MODELS_DIR, fname)
            candidates.append((os.path.getmtime(full), full))
    if not candidates:
        return None
    candidates.sort(reverse=True)
    return candidates[0][1]


# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    p = argparse.ArgumentParser(description="SilentBridge Feedback Ingestion & Retraining")
    p.add_argument("--log",      required=True, help="Path to feedback_log.jsonl from phone")
    p.add_argument("--user",     default="phone_feedback",
                   help="User ID for confirmed samples (default: phone_feedback)")
    p.add_argument("--dry-run",  action="store_true",
                   help="Preview what would happen without writing files or retraining")
    p.add_argument("--no-train", action="store_true",
                   help="Ingest feedback into data/raw/ but skip retraining")
    args = p.parse_args()

    print(f"\nSilentBridge Feedback Ingestion")
    print(f"  Log file:  {args.log}")
    print(f"  User ID:   {args.user}")
    print(f"  Dry run:   {args.dry_run}")
    print()

    # 1. Load log
    if not os.path.exists(args.log):
        print(f"[ERROR] Log file not found: {args.log}")
        sys.exit(1)

    entries = load_log(args.log)
    if not entries:
        print("No entries found. Exiting.")
        sys.exit(0)

    # 2. Summary
    print_summary(entries)

    # 3. Process entries
    confirmed_count = 0
    review_count    = 0
    skipped_count   = 0

    for entry in entries:
        if entry.get("confirmed") is True:
            result = save_confirmed(entry, args.user, args.dry_run)
            print(f"  [YES] {entry.get('predicted', '?'):12s}  conf={entry.get('confidence', 0):.2f}  {result}")
            if "SAVED" in result or "DRY" in result:
                confirmed_count += 1
            else:
                skipped_count += 1
        elif entry.get("confirmed") is False:
            result = save_for_review(entry, args.dry_run)
            print(f"  [NO]  {entry.get('predicted', '?'):12s}  conf={entry.get('confidence', 0):.2f}  {result}")
            review_count += 1
        else:
            print(f"  [SKIP] Entry missing 'confirmed' field.")
            skipped_count += 1

    print(f"\n── Ingestion complete ──")
    print(f"  Added to training data: {confirmed_count}")
    print(f"  Saved for review:       {review_count}  (in data/review/)")
    print(f"  Skipped:                {skipped_count}")

    if review_count > 0:
        print(f"\n  ℹ  Open files in data/review/, set 'true_label', and move them to")
        print(f"     data/raw/<TRUE_LABEL>/<TRUE_LABEL>_XXXX.json before retraining.")

    # 4. Retrain
    if args.no_train:
        print("\nSkipping retraining (--no-train). Run manually when ready:")
        print(f"  python ml/src/preprocess_pipeline.py")
        print(f"  python ml/src/train.py --arch cnn --augment --quantize")
        return

    if confirmed_count == 0 and not args.dry_run:
        print("\nNo new confirmed samples added. Skipping retraining.")
        return

    print("\n── Starting retraining ──")
    run_retraining(args.dry_run)

    # 5. Deploy instructions
    tflite_path = find_tflite(args.dry_run)
    if tflite_path:
        phone_path = "/sdcard/Android/data/com.example.gloves/files/new_model.tflite"
        print(f"\n── New model ready ──")
        print(f"  {tflite_path}")
        print(f"\n  Deploy to phone:")
        print(f"  adb push \"{tflite_path}\" {phone_path}")
        print(f"\n  The app will need to be updated to load from this path,")
        print(f"  or copy it manually to the assets/ folder and rebuild.")
    else:
        print("\n[WARN] No .tflite file found in ml/models/. Check training output.")


if __name__ == "__main__":
    main()