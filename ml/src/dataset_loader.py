"""
SilentBridge — Multi-User Dataset Loader

Supports two folder layouts:

  Legacy (single-user):
    data/raw/HELLO/HELLO_0001.json

  Multi-user (new):
    data/raw/user_001/HELLO/HELLO_0001.json
    data/raw/user_002/HELLO/HELLO_0001.json

Automatically detects which layout is present and handles both.
Each returned recording dict gains a 'user_id' key.
"""

import os
import json
import glob
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import RAW_DATA_DIR, FEATURES


class DatasetLoader:
    def __init__(self, raw_dir=None):
        self.raw_dir = raw_dir or RAW_DATA_DIR

    # ── Layout detection ────────────────────────────────────────────────────
    def _is_multi_user(self):
        """
        Returns True if the raw dir contains user_XXX subdirectories.
        Returns False for the legacy flat layout (LABEL/ directly under raw/).
        """
        if not os.path.exists(self.raw_dir):
            return False
        entries = os.listdir(self.raw_dir)
        return any(
            e.startswith("user_") and os.path.isdir(os.path.join(self.raw_dir, e))
            for e in entries
        )

    # ── User enumeration ────────────────────────────────────────────────────
    def get_user_ids(self):
        """Returns sorted list of user IDs present in the dataset."""
        if not self._is_multi_user():
            return ["user_000"]  # legacy: treat as single anonymous user
        entries = sorted(os.listdir(self.raw_dir))
        return [
            e for e in entries
            if e.startswith("user_") and os.path.isdir(os.path.join(self.raw_dir, e))
        ]

    # ── File discovery ──────────────────────────────────────────────────────
    def _get_label_dirs(self, user_root):
        """Returns {label: path} dict for all label subdirs under user_root."""
        if not os.path.exists(user_root):
            return {}
        return {
            d: os.path.join(user_root, d)
            for d in sorted(os.listdir(user_root))
            if os.path.isdir(os.path.join(user_root, d))
        }

    # ── Single-file validation ───────────────────────────────────────────────
    def _validate_and_load(self, file_path, user_id):
        """Load one JSON file, validate schema, return dict or None."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"  [SKIP] {file_path}: Cannot read JSON — {e}")
            return None

        # Required root keys
        for key in ("label", "frame_count", "frames"):
            if key not in data:
                print(f"  [SKIP] {file_path}: Missing key '{key}'")
                return None

        if data["frame_count"] <= 0 or not data["frames"]:
            print(f"  [SKIP] {file_path}: Empty frames array")
            return None

        if data["frame_count"] != len(data["frames"]):
            print(f"  [WARN] {file_path}: frame_count mismatch — using actual length")
            data["frame_count"] = len(data["frames"])

        # Frame-level feature validation
        for i, frame in enumerate(data["frames"]):
            missing = [f for f in FEATURES if f not in frame]
            if missing:
                print(f"  [SKIP] {file_path}: Frame {i} missing features {missing}")
                return None

        # Attach user metadata
        data["user_id"] = user_id
        if "sample_id" not in data:
            data["sample_id"] = os.path.splitext(os.path.basename(file_path))[0]

        return data

    # ── Public API ───────────────────────────────────────────────────────────
    def load_and_validate(self, user_filter=None):
        """
        Load all valid recordings.

        Args:
            user_filter: list of user_ids to include, or None for all users.

        Returns:
            List of recording dicts, each with a 'user_id' field.
        """
        recordings = []
        skipped = 0

        if self._is_multi_user():
            user_ids = self.get_user_ids()
            if user_filter:
                user_ids = [u for u in user_ids if u in user_filter]

            for user_id in user_ids:
                user_root = os.path.join(self.raw_dir, user_id)
                label_dirs = self._get_label_dirs(user_root)
                for label, label_dir in label_dirs.items():
                    files = sorted(glob.glob(os.path.join(label_dir, "*.json")))
                    for fp in files:
                        rec = self._validate_and_load(fp, user_id)
                        if rec:
                            recordings.append(rec)
                        else:
                            skipped += 1
        else:
            # Legacy single-user layout
            label_dirs = self._get_label_dirs(self.raw_dir)
            for label, label_dir in label_dirs.items():
                files = sorted(glob.glob(os.path.join(label_dir, "*.json")))
                for fp in files:
                    rec = self._validate_and_load(fp, "user_000")
                    if rec:
                        recordings.append(rec)
                    else:
                        skipped += 1

        print(f"Loaded {len(recordings)} valid recordings, skipped {skipped}.")
        return recordings

    def load_for_loso(self):
        """
        Convenience method: returns (recordings, user_ids) ready for
        Leave-One-Subject-Out cross-validation.
        """
        recordings = self.load_and_validate()
        user_ids = sorted(set(r["user_id"] for r in recordings))
        return recordings, user_ids