"""
SilentBridge — Data Augmentation Pipeline

Implements four augmentation strategies from the roadmap:

  1. SensorNoise         — Gaussian noise on all channels
  2. TimeStretching      — Speed up / slow down, then resample back to 100f
  3. FingerScaling       — Scale Hall sensor (finger bend) amplitude
  4. IMURotation         — Perturb pitch, roll, accelerometer values

Usage:
    augmenter = GestureAugmenter(target_len=100, seed=42)
    X_aug, y_aug = augmenter.augment_dataset(X, y, copies_per_sample=5)

X must be shape (N, 100, 13) with features in the canonical order:
    [thumb, index, middle, ring, little, ax, ay, az, gx, gy, gz, pitch, roll]
"""

import numpy as np
from scipy.interpolate import interp1d
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import TARGET_FRAMES, FEATURES, HALL_SENSORS, MPU_FEATURES

# Column index lookups (must match config.py FEATURES list)
HALL_COLS   = [FEATURES.index(f) for f in HALL_SENSORS]                  # 0–4
ACCEL_COLS  = [FEATURES.index(f) for f in ["ax", "ay", "az"]]           # 5–7
GYRO_COLS   = [FEATURES.index(f) for f in ["gx", "gy", "gz"]]           # 8–10
PITCH_COL   = FEATURES.index("pitch")                                     # 11
ROLL_COL    = FEATURES.index("roll")                                      # 12


class GestureAugmenter:
    """
    Applies randomised augmentation to (N, 100, 13) tensors.
    All augmentations are applied to a copy — originals are untouched.
    """

    def __init__(
        self,
        target_len: int = TARGET_FRAMES,
        seed: int = 42,
        # ── Noise ───────────────────────────────────────────────
        noise_std: float = 0.02,           # σ relative to normalised range [0,1]
        # ── Time stretching ─────────────────────────────────────
        time_stretch_range: tuple = (0.7, 1.3),   # speed factor relative to 1.0
        # ── Finger scaling ──────────────────────────────────────
        finger_scale_range: tuple = (0.8, 1.2),
        # ── IMU rotation ────────────────────────────────────────
        pitch_jitter_deg: float = 10.0,    # ±degrees
        roll_jitter_deg:  float = 10.0,
        accel_jitter:     float = 0.05,    # ±g
    ):
        self.target_len          = target_len
        self.rng                 = np.random.default_rng(seed)
        self.noise_std           = noise_std
        self.time_stretch_range  = time_stretch_range
        self.finger_scale_range  = finger_scale_range
        self.pitch_jitter_deg    = pitch_jitter_deg
        self.roll_jitter_deg     = roll_jitter_deg
        self.accel_jitter        = accel_jitter

    # ── Individual augmentation methods ─────────────────────────────────────

    def sensor_noise(self, sample: np.ndarray) -> np.ndarray:
        """
        Add independent Gaussian noise to every channel.
        sample: (100, 13)
        """
        noise = self.rng.normal(0, self.noise_std, size=sample.shape).astype(np.float32)
        out = sample + noise
        # Clip Hall sensors (already normalised to [0,1]) back into range
        out[:, HALL_COLS] = np.clip(out[:, HALL_COLS], 0.0, 1.0)
        return out

    def time_stretch(self, sample: np.ndarray) -> np.ndarray:
        """
        Randomly stretch or compress the gesture in time, then resample
        back to target_len frames using linear interpolation.
        sample: (100, 13)
        """
        lo, hi = self.time_stretch_range
        factor = self.rng.uniform(lo, hi)
        stretched_len = max(10, int(self.target_len * factor))

        if stretched_len == self.target_len:
            return sample.copy()

        x_old = np.linspace(0, 1, self.target_len)
        x_new = np.linspace(0, 1, stretched_len)
        x_out = np.linspace(0, 1, self.target_len)

        out = np.zeros_like(sample)
        for col in range(sample.shape[1]):
            # Stretch
            f_stretch = interp1d(x_old, sample[:, col], kind="linear")
            stretched  = f_stretch(x_new)
            # Resample back to target_len
            f_resamp   = interp1d(x_new, stretched, kind="linear")
            out[:, col] = f_resamp(x_out)

        return out.astype(np.float32)

    def finger_scaling(self, sample: np.ndarray) -> np.ndarray:
        """
        Scale Hall sensor values (finger bend amplitude) by a random factor.
        Simulates loose/tight glove fit or flexible/stiff fingers.
        sample: (100, 13)
        """
        lo, hi = self.finger_scale_range
        out = sample.copy()
        for col in HALL_COLS:
            scale = self.rng.uniform(lo, hi)
            out[:, col] = np.clip(out[:, col] * scale, 0.0, 1.0)
        return out

    def imu_rotation(self, sample: np.ndarray) -> np.ndarray:
        """
        Perturb pitch, roll, and accelerometer values to simulate
        different wrist orientations and signing angles.
        sample: (100, 13)
        """
        out = sample.copy()

        # Pitch & roll jitter
        pitch_delta = self.rng.uniform(-self.pitch_jitter_deg, self.pitch_jitter_deg)
        roll_delta  = self.rng.uniform(-self.roll_jitter_deg,  self.roll_jitter_deg)
        out[:, PITCH_COL] += pitch_delta
        out[:, ROLL_COL]  += roll_delta

        # Accelerometer jitter (applied independently per axis)
        for col in ACCEL_COLS:
            out[:, col] += self.rng.uniform(-self.accel_jitter, self.accel_jitter)

        return out

    # ── Combined augmentation ────────────────────────────────────────────────

    def augment_one(self, sample: np.ndarray, strategy: str = "random") -> np.ndarray:
        """
        Apply one or more augmentations to a single sample.

        strategy:
          "random"  — randomly pick a subset of augmentations each time
          "all"     — apply every augmentation in sequence
          "noise"   — sensor noise only
          "time"    — time stretch only
          "finger"  — finger scaling only
          "imu"     — IMU rotation only
        """
        out = sample.copy()

        if strategy == "noise":
            out = self.sensor_noise(out)
        elif strategy == "time":
            out = self.time_stretch(out)
        elif strategy == "finger":
            out = self.finger_scaling(out)
        elif strategy == "imu":
            out = self.imu_rotation(out)
        elif strategy == "all":
            out = self.sensor_noise(out)
            out = self.time_stretch(out)
            out = self.finger_scaling(out)
            out = self.imu_rotation(out)
        else:  # "random"
            # Each augmentation is applied independently with p=0.5
            if self.rng.random() > 0.5:
                out = self.sensor_noise(out)
            if self.rng.random() > 0.5:
                out = self.time_stretch(out)
            if self.rng.random() > 0.5:
                out = self.finger_scaling(out)
            if self.rng.random() > 0.5:
                out = self.imu_rotation(out)

        return out

    def augment_dataset(
        self,
        X: np.ndarray,
        y: np.ndarray,
        copies_per_sample: int = 5,
        strategy: str = "random",
        include_originals: bool = True,
    ) -> tuple:
        """
        Generate augmented copies for every sample in the dataset.

        Args:
            X: (N, 100, 13) float32
            y: (N,) int32 class labels
            copies_per_sample: how many augmented versions to generate per original
            strategy: see augment_one()
            include_originals: if True, originals are prepended to the output

        Returns:
            X_aug: ((copies_per_sample [+ 1]) * N, 100, 13)
            y_aug: matching labels
        """
        N = X.shape[0]
        copies = [self.augment_one(X[i], strategy) for _ in range(copies_per_sample) for i in range(N)]
        X_copies = np.array(copies, dtype=np.float32).reshape(copies_per_sample, N, *X.shape[1:])
        # copies_per_sample × N → (copies_per_sample*N, 100, 13)
        X_copies = X_copies.reshape(copies_per_sample * N, *X.shape[1:])
        y_copies = np.tile(y, copies_per_sample)

        if include_originals:
            X_aug = np.concatenate([X, X_copies], axis=0)
            y_aug = np.concatenate([y, y_copies], axis=0)
        else:
            X_aug, y_aug = X_copies, y_copies

        # Shuffle
        idx = self.rng.permutation(len(X_aug))
        return X_aug[idx], y_aug[idx]

    # ── Per-class augmentation (balances class distribution) ─────────────────
    def augment_to_balance(
        self,
        X: np.ndarray,
        y: np.ndarray,
        strategy: str = "random",
    ) -> tuple:
        """
        Augment under-represented classes so every class reaches the count
        of the largest class.  Originals are always included.
        """
        classes, counts = np.unique(y, return_counts=True)
        target_count = counts.max()

        X_out = [X]
        y_out = [y]

        for cls, count in zip(classes, counts):
            if count >= target_count:
                continue
            needed = target_count - count
            cls_mask = (y == cls)
            X_cls = X[cls_mask]
            generated = []
            while len(generated) < needed:
                idx = self.rng.integers(0, len(X_cls))
                generated.append(self.augment_one(X_cls[idx], strategy))
            X_out.append(np.array(generated[:needed], dtype=np.float32))
            y_out.append(np.full(needed, cls, dtype=y.dtype))

        X_aug = np.concatenate(X_out, axis=0)
        y_aug = np.concatenate(y_out, axis=0)
        idx = self.rng.permutation(len(X_aug))
        return X_aug[idx], y_aug[idx]


# ── Quick smoke-test ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    rng = np.random.default_rng(0)
    X_dummy = rng.random((10, 100, 13)).astype(np.float32)
    y_dummy = np.array([0, 1, 2, 3, 4, 5, 6, 7, 0, 1], dtype=np.int32)

    aug = GestureAugmenter(seed=0)

    X_aug, y_aug = aug.augment_dataset(X_dummy, y_dummy, copies_per_sample=5)
    print(f"augment_dataset: {X_dummy.shape} → {X_aug.shape}")
    assert X_aug.shape == (60, 100, 13), X_aug.shape

    X_bal, y_bal = aug.augment_to_balance(X_dummy, y_dummy)
    print(f"augment_to_balance: labels {dict(zip(*np.unique(y_bal, return_counts=True)))}")
    print("Augmentation smoke-test PASSED.")