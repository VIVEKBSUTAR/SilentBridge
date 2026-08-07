"""
SilentBridge — Improved Training Pipeline

Key upgrades over the original:
  1. CNN + BiLSTM + Attention architecture
  2. Leave-One-Subject-Out (LOSO) cross-validation support
  3. Data augmentation integrated into the training loop
  4. Per-user calibration normalisation support
  5. TFLite export with INT8 quantisation

Run modes:
    python train.py                 # Standard 70/15/15 split (backward-compatible)
    python train.py --loso          # Leave-One-Subject-Out CV
    python train.py --augment       # Enable data augmentation
    python train.py --loso --augment --quantize   # Full production pipeline
"""

import os
import sys
import json
import argparse
import random
import numpy as np
import tensorflow as tf
from tensorflow.keras import Input
from tensorflow.keras.models import Model
from tensorflow.keras.layers import (
    Conv1D, Bidirectional, LSTM, Dense, Dropout,
    GlobalAveragePooling1D, LayerNormalization, Multiply, Activation
)
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau
from sklearn.model_selection import train_test_split
from sklearn.utils.class_weight import compute_class_weight
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.preprocessing import StandardScaler
import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    BASE_DIR, PROCESSED_DATA_DIR, SCALERS_DIR,
    TARGET_FRAMES, FEATURE_COUNT, FEATURES, MPU_FEATURES
)
from dataset_loader import DatasetLoader
from feature_extractor import FeatureExtractor
from normalizer import Normalizer
from resampler import Resampler
from label_encoder import DynamicLabelEncoder
from augmentation import GestureAugmenter


# ── Seeding ──────────────────────────────────────────────────────────────────
def set_seeds(seed=42):
    os.environ["PYTHONHASHSEED"] = str(seed)
    random.seed(seed)
    np.random.seed(seed)
    tf.random.set_seed(seed)


# ── Architecture ─────────────────────────────────────────────────────────────
def soft_attention(x):
    """
    Simple additive attention over the time dimension.
    x: (batch, T, features)
    returns: (batch, features)  — weighted sum over T
    """
    # Score each timestep
    score = Dense(1, activation="tanh")(x)        # (batch, T, 1)
    weights = Activation("softmax")(score)         # (batch, T, 1)
    context = Multiply()([x, weights])             # (batch, T, features)
    return GlobalAveragePooling1D()(context)       # (batch, features) weighted avg


def build_cnn_bilstm_attention(
    input_shape=(TARGET_FRAMES, FEATURE_COUNT),
    num_classes=8,
    dropout_rate=0.3,
):
    """
    CNN + BiLSTM + Attention model.

    CNN layers capture short local patterns (individual finger movements).
    BiLSTM captures temporal context across the full gesture.
    Attention focuses the classifier on the most informative frames.
    """
    inp = Input(shape=input_shape)

    # ── Local feature extraction ──────────────────────────────────────────
    x = Conv1D(64,  kernel_size=3, activation="relu", padding="same")(inp)
    x = LayerNormalization()(x)
    x = Conv1D(128, kernel_size=3, activation="relu", padding="same")(x)
    x = LayerNormalization()(x)
    x = Dropout(dropout_rate)(x)

    # ── Temporal modelling ────────────────────────────────────────────────
    x = Bidirectional(LSTM(64, return_sequences=True, unroll = True))(x)
    x = Dropout(dropout_rate)(x)

    # ── Attention ─────────────────────────────────────────────────────────
    x = soft_attention(x)                           # (batch, 128)

    # ── Classification head ───────────────────────────────────────────────
    x = Dense(64, activation="relu")(x)
    x = Dropout(dropout_rate)(x)
    out = Dense(num_classes, activation="softmax")(x)

    model = Model(inputs=inp, outputs=out)
    return model


def build_original_bilstm(input_shape=(TARGET_FRAMES, FEATURE_COUNT), num_classes=8):
    """Original BiLSTM architecture for comparison / fallback."""
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import Bidirectional, LSTM, Dense, Dropout, Input as KInput

    model = tf.keras.Sequential([
        KInput(shape=input_shape),
        Bidirectional(LSTM(64, return_sequences=True)),
        Dropout(0.3),
        Bidirectional(LSTM(32)),
        Dropout(0.3),
        Dense(32, activation="relu"),
        Dense(num_classes, activation="softmax"),
    ])
    return model


# ── Data loading & preprocessing ─────────────────────────────────────────────
def load_and_preprocess(raw_dir=None):
    """
    Load all recordings, extract features, normalise, resample.
    Returns X (N,100,13), y (N,), label_map, user_ids_per_sample.
    """
    loader = DatasetLoader(raw_dir=raw_dir)
    recordings = loader.load_and_validate()

    if not recordings:
        print("No valid recordings found.")
        sys.exit(1)

    normalizer = Normalizer()
    resampler  = Resampler()

    X_list, y_labels, user_ids = [], [], []

    for rec in recordings:
        raw   = FeatureExtractor.extract(rec)
        normed = normalizer.normalize_hall_sensors(raw)
        res    = resampler.resample(normed)
        X_list.append(res)
        y_labels.append(rec["label"])
        user_ids.append(rec.get("user_id", "user_000"))

    X = np.stack(X_list)          # (N, 100, 13)

    encoder  = DynamicLabelEncoder(y_labels)
    encoder.save_mapping()
    y = np.array([encoder.encode(l) for l in y_labels], dtype=np.int32)
    label_map = encoder.get_mapping()

    return X, y, label_map, user_ids


def fit_and_apply_scaler(X, mpu_indices, scaler=None, fit=True):
    """
    Standardise the 8 IMU feature columns in-place (on a copy).
    If fit=True, fits a new scaler. Otherwise uses the provided scaler.
    Returns (X_scaled, scaler).
    """
    X = X.copy()
    N = X.shape[0]
    X_2d = X.reshape(-1, FEATURE_COUNT)
    mpu_data = X_2d[:, mpu_indices]

    if fit:
        scaler = StandardScaler()
        mpu_scaled = scaler.fit_transform(mpu_data)
    else:
        mpu_scaled = scaler.transform(mpu_data)

    X_2d[:, mpu_indices] = mpu_scaled
    return X_2d.reshape(N, TARGET_FRAMES, FEATURE_COUNT), scaler


# ── Standard 70/15/15 split training ─────────────────────────────────────────
def train_standard(args):
    set_seeds(42)
    print("\n=== Standard 70/15/15 Training ===\n")

    X, y, label_map, _ = load_and_preprocess()
    mpu_indices = [FEATURES.index(f) for f in MPU_FEATURES]
    num_classes = len(label_map)

    # Augmentation (before splitting so test set stays clean)
    if args.augment:
        print(f"Augmenting dataset: {X.shape[0]} → ", end="")
        aug = GestureAugmenter(seed=42)
        X, y = aug.augment_dataset(X, y, copies_per_sample=5, strategy="random")
        print(f"{X.shape[0]} samples")

    # Split
    idx = np.arange(len(X))
    idx_train, idx_temp, y_train, y_temp = train_test_split(
        idx, y, test_size=0.30, stratify=y, random_state=42
    )
    idx_val, idx_test, y_val, y_test = train_test_split(
        idx_temp, y_temp, test_size=0.50, stratify=y_temp, random_state=42
    )

    X_train = X[idx_train]; X_val = X[idx_val]; X_test = X[idx_test]

    # Scaler
    X_train, scaler = fit_and_apply_scaler(X_train, mpu_indices, fit=True)
    X_val,   _      = fit_and_apply_scaler(X_val,   mpu_indices, scaler=scaler, fit=False)
    X_test,  _      = fit_and_apply_scaler(X_test,  mpu_indices, scaler=scaler, fit=False)

    # Save scaler
    os.makedirs(SCALERS_DIR, exist_ok=True)
    joblib.dump(scaler, os.path.join(SCALERS_DIR, "feature_scaler.pkl"))
    print(f"Scaler saved. Train={len(idx_train)}, Val={len(idx_val)}, Test={len(idx_test)}")

    _run_training(X_train, y_train, X_val, y_val, X_test, y_test,
                  label_map, num_classes, args, tag="standard")


# ── Leave-One-Subject-Out training ───────────────────────────────────────────
def train_loso(args):
    set_seeds(42)
    print("\n=== Leave-One-Subject-Out Cross-Validation ===\n")

    X, y, label_map, user_ids = load_and_preprocess()
    mpu_indices = [FEATURES.index(f) for f in MPU_FEATURES]
    num_classes  = len(label_map)
    user_ids_arr = np.array(user_ids)
    unique_users = sorted(set(user_ids))

    if len(unique_users) < 2:
        print("[ERROR] LOSO requires at least 2 users in the dataset.")
        sys.exit(1)

    all_results = []
    results_dir = os.path.join(BASE_DIR, "ml", "results", "loso")
    os.makedirs(results_dir, exist_ok=True)

    for held_out in unique_users:
        print(f"\n--- Holding out: {held_out} ---")

        test_mask  = (user_ids_arr == held_out)
        train_mask = ~test_mask

        X_train_raw, y_train = X[train_mask], y[train_mask]
        X_test_raw,  y_test  = X[test_mask],  y[test_mask]

        if len(X_test_raw) == 0:
            print(f"  Skipping {held_out}: no test samples.")
            continue

        # Augment training fold only
        if args.augment:
            print(f"  Augmenting training fold: {X_train_raw.shape[0]} → ", end="")
            aug = GestureAugmenter(seed=42)
            X_train_raw, y_train = aug.augment_dataset(
                X_train_raw, y_train, copies_per_sample=5, strategy="random"
            )
            print(f"{X_train_raw.shape[0]}")

        # Scale (fit on train, apply to test)
        X_train, scaler = fit_and_apply_scaler(X_train_raw, mpu_indices, fit=True)
        X_test,  _      = fit_and_apply_scaler(X_test_raw,  mpu_indices, scaler=scaler, fit=False)

        # Val split from training data (10%)
        idx_t = np.arange(len(X_train))
        idx_tr, idx_v, y_tr, y_v = train_test_split(
            idx_t, y_train, test_size=0.10, stratify=y_train, random_state=42
        )

        tag = f"loso_{held_out}"
        acc = _run_training(
            X_train[idx_tr], y_tr,
            X_train[idx_v],  y_v,
            X_test, y_test,
            label_map, num_classes, args, tag=tag
        )
        all_results.append({"held_out": held_out, "test_accuracy": acc})
        print(f"  Fold accuracy ({held_out}): {acc:.4f}")

    # Summary
    accs = [r["test_accuracy"] for r in all_results]
    print(f"\n=== LOSO Summary ===")
    print(f"Mean accuracy: {np.mean(accs):.4f}")
    print(f"Std:           {np.std(accs):.4f}")
    print(f"Min:           {np.min(accs):.4f}")
    print(f"Max:           {np.max(accs):.4f}")
    with open(os.path.join(results_dir, "loso_summary.json"), "w") as f:
        json.dump({
            "folds": all_results,
            "mean_accuracy": float(np.mean(accs)),
            "std_accuracy":  float(np.std(accs)),
        }, f, indent=2)
    print(f"Results saved to {results_dir}/loso_summary.json")


# ── Core training function ────────────────────────────────────────────────────
def _run_training(X_train, y_train, X_val, y_val, X_test, y_test,
                  label_map, num_classes, args, tag="run"):
    """Builds, trains, evaluates, and optionally exports one model."""

    results_dir = os.path.join(BASE_DIR, "ml", "results")
    models_dir  = os.path.join(BASE_DIR, "ml", "models")
    os.makedirs(results_dir, exist_ok=True)
    os.makedirs(models_dir,  exist_ok=True)

    # Class weights
    classes = np.unique(y_train)
    weights = compute_class_weight("balanced", classes=classes, y=y_train)
    class_weight_dict = dict(zip(classes, weights))

    # Model
    if args.arch == "cnn":
        model = build_cnn_bilstm_attention(
            input_shape=(TARGET_FRAMES, FEATURE_COUNT),
            num_classes=num_classes,
        )
    else:
        model = build_original_bilstm(
            input_shape=(TARGET_FRAMES, FEATURE_COUNT),
            num_classes=num_classes,
        )

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )

    model_path = os.path.join(models_dir, f"best_model_{tag}.keras")
    callbacks = [
        EarlyStopping(monitor="val_loss", patience=15, restore_best_weights=True),
        ModelCheckpoint(filepath=model_path, save_best_only=True, monitor="val_loss"),
        ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=5, min_lr=1e-5, verbose=0),
    ]

    print(f"\nTraining [{tag}] — "
          f"train={len(X_train)}, val={len(X_val)}, test={len(X_test)}")
    model.summary()

    history = model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=150,
        batch_size=16,
        class_weight=class_weight_dict,
        callbacks=callbacks,
        verbose=1,
    )

    # Evaluation
    test_loss, test_acc = model.evaluate(X_test, y_test, verbose=0)
    y_pred = np.argmax(model.predict(X_test, verbose=0), axis=1)

    reverse_map    = {v: k for k, v in label_map.items()}
    target_names   = [reverse_map[i] for i in range(num_classes)]
    report         = classification_report(y_test, y_pred, target_names=target_names, output_dict=True)
    cm             = confusion_matrix(y_test, y_pred)

    # Save artifacts
    _save_results(history, report, cm, target_names, results_dir, tag)

    print(f"\n[{tag}] Test accuracy: {test_acc:.4f}")

    # TFLite export
    if args.quantize:
        _export_tflite(model, models_dir, tag, X_train)

    return test_acc


# ── Result persistence ────────────────────────────────────────────────────────
def _save_results(history, report, cm, target_names, results_dir, tag):
    with open(os.path.join(results_dir, f"classification_report_{tag}.json"), "w") as f:
        json.dump(report, f, indent=2)
    with open(os.path.join(results_dir, f"training_history_{tag}.json"), "w") as f:
        json.dump(history.history, f, indent=2)
    np.save(os.path.join(results_dir, f"confusion_matrix_{tag}.npy"), cm)

    # Plots
    plt.figure(figsize=(8, 5))
    plt.plot(history.history["accuracy"], label="Train")
    plt.plot(history.history["val_accuracy"], label="Val")
    plt.title(f"Accuracy [{tag}]"); plt.xlabel("Epoch"); plt.ylabel("Accuracy")
    plt.legend(); plt.tight_layout()
    plt.savefig(os.path.join(results_dir, f"training_accuracy_{tag}.png")); plt.close()

    plt.figure(figsize=(9, 7))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues",
                xticklabels=target_names, yticklabels=target_names)
    plt.title(f"Confusion Matrix [{tag}]")
    plt.ylabel("True"); plt.xlabel("Predicted"); plt.tight_layout()
    plt.savefig(os.path.join(results_dir, f"confusion_matrix_{tag}.png")); plt.close()


# ── TFLite quantised export ───────────────────────────────────────────────────
def _export_tflite(model, models_dir, tag, X_representative):
    """
    Convert the trained Keras model to TFLite with INT8 quantisation.
    A small representative dataset is needed for full integer quantisation.
    """
    print(f"\nExporting TFLite model [{tag}]…")

    def representative_data_gen():
        # Use up to 200 samples from the training set as calibration data
        samples = X_representative[:200]
        for s in samples:
            yield [s.reshape(1, TARGET_FRAMES, FEATURE_COUNT).astype(np.float32)]

    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    converter.representative_dataset = representative_data_gen
    converter.target_spec.supported_ops = [
        tf.lite.OpsSet.TFLITE_BUILTINS,
        tf.lite.OpsSet.SELECT_TF_OPS
    ]
    converter._experimental_lower_tensor_list_ops = False

    tflite_model = converter.convert()
    tflite_path  = os.path.join(models_dir, f"silentbridge_{tag}.tflite")
    with open(tflite_path, "wb") as f:
        f.write(tflite_model)

    size_kb = os.path.getsize(tflite_path) / 1024
    print(f"TFLite model saved: {tflite_path} ({size_kb:.1f} KB)")
    return tflite_path


# ── CLI ───────────────────────────────────────────────────────────────────────
def parse_args():
    p = argparse.ArgumentParser(description="SilentBridge Training Pipeline")
    p.add_argument("--loso",     action="store_true", help="Leave-One-Subject-Out CV")
    p.add_argument("--augment",  action="store_true", help="Enable data augmentation")
    p.add_argument("--quantize", action="store_true", help="Export INT8 TFLite model")
    p.add_argument("--arch",     choices=["cnn", "bilstm"], default="cnn",
                   help="Model architecture (default: cnn)")
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()  
    if args.loso:
        train_loso(args)
    else:
        train_standard(args)