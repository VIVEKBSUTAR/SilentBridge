"""
SilentBridge — Dataset Manager (v2, Multi-User)

save_recording() now accepts an optional user_id.
  - If user_id is provided → saves to data/raw/user_XXX/LABEL/LABEL_NNNN.json
  - If user_id is None     → saves to data/raw/LABEL/LABEL_NNNN.json  (legacy)

All other behaviour (sequential naming, validation, schema) is unchanged.
"""

import os
import json
import glob
from datetime import datetime
from config import DATASET_PATH


REQUIRED_FRAME_KEYS = {
    "timestamp", "thumb", "index", "middle", "ring", "little",
    "ax", "ay", "az", "gx", "gy", "gz", "pitch", "roll"
}


# ── Path helpers ─────────────────────────────────────────────────────────────
def _label_dir(label: str, user_id: str = None) -> str:
    """Returns the full path to the label directory for the given user."""
    if user_id:
        return os.path.join(DATASET_PATH, user_id, label)
    return os.path.join(DATASET_PATH, label)


def create_label_directory(label: str, user_id: str = None) -> str:
    path = _label_dir(label, user_id)
    os.makedirs(path, exist_ok=True)
    return path


def count_existing_samples(label: str, user_id: str = None) -> int:
    path = _label_dir(label, user_id)
    if not os.path.exists(path):
        return 0
    return len(glob.glob(os.path.join(path, f"{label}_*.json")))


def get_next_sample_id(label: str, user_id: str = None) -> str:
    path = _label_dir(label, user_id)
    if not os.path.exists(path):
        return f"{label}_0001"

    files = glob.glob(os.path.join(path, f"{label}_*.json"))
    max_num = 0
    for fp in files:
        basename = os.path.basename(fp)
        try:
            num = int(basename.replace(f"{label}_", "").replace(".json", ""))
            if num > max_num:
                max_num = num
        except ValueError:
            pass
    return f"{label}_{max_num + 1:04d}"


# ── Validation ───────────────────────────────────────────────────────────────
def validate_recording(frames: list) -> bool:
    if not frames:
        return False
    for frame in frames:
        if not REQUIRED_FRAME_KEYS.issubset(frame.keys()):
            return False
    return True


# ── Save ─────────────────────────────────────────────────────────────────────
def save_recording(label: str, frames: list, user_id: str = None) -> str:
    """
    Save a gesture recording to disk.

    Args:
        label:   Gesture class name (e.g. "HELLO")
        frames:  List of raw JSON packets from SerialReader
        user_id: Optional user ID (e.g. "user_001"). If provided, saves under
                 data/raw/user_001/HELLO/. If None, saves flat (legacy layout).

    Returns:
        Path to the saved file.
    """
    if not validate_recording(frames):
        raise ValueError("Invalid recording: missing required frame keys.")

    create_label_directory(label, user_id)
    sample_id = get_next_sample_id(label, user_id)

    recording = {
        "label":       label,
        "sample_id":   sample_id,
        "user_id":     user_id or "user_000",
        "recorded_at": datetime.now().isoformat(),
        "frame_count": len(frames),
        "frames":      frames,
    }

    file_path = os.path.join(_label_dir(label, user_id), f"{sample_id}.json")
    with open(file_path, "w") as f:
        json.dump(recording, f, indent=2)

    return file_path