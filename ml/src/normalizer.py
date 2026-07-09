"""
SilentBridge — Normalizer

Two normalization modes:

  1. GlobalNormalizer   — original /4095 approach (used during training when
                          no per-user calibration data is available)

  2. UserNormalizer     — per-user min/max calibration approach (recommended).
                          Uses open-hand and closed-fist readings to map each
                          user's actual sensor range to [0, 1].
"""

import os
import sys
import json
import numpy as np

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import FEATURES, HALL_SENSORS


# ── Global normalizer (original behaviour) ──────────────────────────────────
class Normalizer:
    """
    Original normalizer: divides Hall sensor readings by 4095.
    Kept for backward compatibility with existing trained model.
    """
    def __init__(self):
        self.hall_indices = [FEATURES.index(s) for s in HALL_SENSORS]

    def normalize_hall_sensors(self, array_2d):
        """
        array_2d: (N_frames, 13) float32
        Returns a copy with Hall columns scaled to [0, 1].
        """
        out = array_2d.copy()
        for idx in self.hall_indices:
            out[:, idx] = np.clip(out[:, idx] / 4095.0, 0.0, 1.0)
        return out


# ── Per-user calibration normalizer (new, recommended) ──────────────────────
class UserNormalizer:
    """
    Per-user min/max normalization.

    Uses calibration measurements collected from each individual user:
      - open_values:   raw ADC readings with hand fully open (relaxed)
      - closed_values: raw ADC readings with hand fully closed (fist)

    Formula:
        normalized = (sensor - open_value) / (closed_value - open_value)

    This maps every user's personal sensor range to [0, 1], eliminating
    hardware offset and individual hand-size variation.
    """

    FINGER_ORDER = ["thumb", "index", "middle", "ring", "little"]

    def __init__(self):
        self.hall_indices = [FEATURES.index(s) for s in HALL_SENSORS]
        self.open_values  = None   # shape: (5,)  one per finger
        self.closed_values = None  # shape: (5,)

    # ── Calibration data ingestion ──────────────────────────────────────────
    def set_calibration(self, open_values: dict, closed_values: dict):
        """
        open_values:   {"thumb": 900, "index": 850, ...}
        closed_values: {"thumb": 3100, "index": 2900, ...}
        """
        self.open_values   = np.array([open_values[f]   for f in self.FINGER_ORDER], dtype=np.float32)
        self.closed_values = np.array([closed_values[f] for f in self.FINGER_ORDER], dtype=np.float32)
        self._validate()

    def load_calibration(self, path: str):
        """Load calibration from a JSON file (saved by the Android app)."""
        with open(path, "r") as f:
            cal = json.load(f)
        self.set_calibration(cal["open"], cal["closed"])

    def save_calibration(self, path: str):
        """Persist calibration so it can be reloaded later."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        cal = {
            "open":   {f: float(v) for f, v in zip(self.FINGER_ORDER, self.open_values)},
            "closed": {f: float(v) for f, v in zip(self.FINGER_ORDER, self.closed_values)},
        }
        with open(path, "w") as f:
            json.dump(cal, f, indent=2)

    def _validate(self):
        assert self.open_values is not None and self.closed_values is not None
        ranges = self.closed_values - self.open_values
        near_zero = np.where(np.abs(ranges) < 50)[0]
        if len(near_zero) > 0:
            bad = [self.FINGER_ORDER[i] for i in near_zero]
            print(f"[WARNING] Very small calibration range for: {bad}. "
                  "Check that the user fully opened/closed their hand during calibration.")

    # ── Normalization ────────────────────────────────────────────────────────
    def normalize_hall_sensors(self, array_2d):
        """
        array_2d: (N_frames, 13) float32
        Returns a copy with Hall columns scaled per-user to [0, 1].
        Falls back to /4095 if calibration has not been set.
        """
        if self.open_values is None or self.closed_values is None:
            print("[WARNING] UserNormalizer: calibration not set, falling back to /4095")
            out = array_2d.copy()
            for idx in self.hall_indices:
                out[:, idx] = np.clip(out[:, idx] / 4095.0, 0.0, 1.0)
            return out

        out = array_2d.copy()
        ranges = self.closed_values - self.open_values

        for col_pos, feat_idx in enumerate(self.hall_indices):
            raw = out[:, feat_idx]
            norm = (raw - self.open_values[col_pos]) / (ranges[col_pos] + 1e-8)
            out[:, feat_idx] = np.clip(norm, 0.0, 1.0)

        return out

    # ── Calibration from live frames ─────────────────────────────────────────
    @staticmethod
    def compute_calibration_from_frames(open_frames: list, closed_frames: list) -> tuple:
        """
        Given lists of raw JSON packets collected during open/closed calibration,
        computes stable min/max values by taking the median across all frames.

        Returns: (open_values_dict, closed_values_dict)
        """
        fingers = ["thumb", "index", "middle", "ring", "little"]

        def median_readings(frames):
            readings = {f: [] for f in fingers}
            for frame in frames:
                for f in fingers:
                    readings[f].append(frame[f])
            return {f: float(np.median(readings[f])) for f in fingers}

        return median_readings(open_frames), median_readings(closed_frames)