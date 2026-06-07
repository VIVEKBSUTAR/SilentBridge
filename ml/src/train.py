import os
import sys
import json
import random
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Input, LSTM, Bidirectional, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
from sklearn.model_selection import train_test_split
from sklearn.utils.class_weight import compute_class_weight
from sklearn.metrics import classification_report, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import BASE_DIR, PROCESSED_DATA_DIR, TARGET_FRAMES, FEATURE_COUNT

def set_seeds(seed=42):
    os.environ['PYTHONHASHSEED'] = str(seed)
    random.seed(seed)
    np.random.seed(seed)
    tf.random.set_seed(seed)

def main():
    set_seeds(42)
    print("Starting Phase 2B Training Pipeline...")

    # Set up directories
    models_dir = os.path.join(BASE_DIR, "ml", "models")
    results_dir = os.path.join(BASE_DIR, "ml", "results")
    os.makedirs(models_dir, exist_ok=True)
    os.makedirs(results_dir, exist_ok=True)

    # 1. Load Data
    x_path = os.path.join(PROCESSED_DATA_DIR, "X.npy")
    y_path = os.path.join(PROCESSED_DATA_DIR, "y.npy")
    label_map_path = os.path.join(PROCESSED_DATA_DIR, "label_map.json")

    if not (os.path.exists(x_path) and os.path.exists(y_path) and os.path.exists(label_map_path)):
        print("Processed data not found. Please run preprocessing pipeline first.")
        sys.exit(1)

    X = np.load(x_path)
    y = np.load(y_path)

    with open(label_map_path, "r") as f:
        label_map = json.load(f)
    reverse_label_map = {v: k for k, v in label_map.items()}
    num_classes = len(label_map)

    # 2. Tensor Verification
    print("\n--- Tensor Verification ---")
    print(f"X shape: {X.shape}")
    print(f"y shape: {y.shape}")
    print(f"Number of classes: {num_classes}")

    if X.shape[1:] != (TARGET_FRAMES, FEATURE_COUNT):
        print(f"Verification Failed: Expected X shape (*, {TARGET_FRAMES}, {FEATURE_COUNT})")
        sys.exit(1)
    if len(y.shape) != 1 or X.shape[0] != y.shape[0]:
        print("Verification Failed: y shape mismatch")
        sys.exit(1)
    if num_classes != 8:
        print(f"Verification Failed: Expected 8 classes, got {num_classes}")
        sys.exit(1)
    print("Verification Passed.\n")

    # 3. Dataset Split (70/15/15)
    indices = np.arange(X.shape[0])
    # First split: 70% train, 30% temp (val+test)
    idx_train, idx_temp, y_train, y_temp = train_test_split(
        indices, y, test_size=0.30, stratify=y, random_state=42
    )
    # Second split: 15% val, 15% test (which is 50% of the 30% temp)
    idx_val, idx_test, y_val, y_test = train_test_split(
        idx_temp, y_temp, test_size=0.50, stratify=y_temp, random_state=42
    )

    X_train, y_train = X[idx_train], y[idx_train]
    X_val, y_val = X[idx_val], y[idx_val]
    X_test, y_test = X[idx_test], y[idx_test]

    # Save indices
    np.save(os.path.join(PROCESSED_DATA_DIR, "train_indices.npy"), idx_train)
    np.save(os.path.join(PROCESSED_DATA_DIR, "val_indices.npy"), idx_val)
    np.save(os.path.join(PROCESSED_DATA_DIR, "test_indices.npy"), idx_test)
    print(f"Splits saved: Train={len(idx_train)}, Val={len(idx_val)}, Test={len(idx_test)}")

    # 4. Class Weights
    classes = np.unique(y_train)
    weights = compute_class_weight('balanced', classes=classes, y=y_train)
    class_weight_dict = {cls: weight for cls, weight in zip(classes, weights)}
    print(f"\nClass Weights Computed: {class_weight_dict}")

    # 5. Model Architecture
    model = Sequential([
        Input(shape=(TARGET_FRAMES, FEATURE_COUNT)),
        Bidirectional(LSTM(64, return_sequences=True)),
        Dropout(0.3),
        Bidirectional(LSTM(32)),
        Dropout(0.3),
        Dense(32, activation='relu'),
        Dense(num_classes, activation='softmax')
    ])

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
        loss='sparse_categorical_crossentropy',
        metrics=['accuracy']
    )

    # Save Model Summary
    with open(os.path.join(results_dir, "model_summary.txt"), "w") as f:
        model.summary(print_fn=lambda x: f.write(x + '\n'))

    # 6. Callbacks
    best_model_path = os.path.join(models_dir, "best_model.keras")
    callbacks = [
        EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True),
        ModelCheckpoint(filepath=best_model_path, save_best_only=True, monitor='val_loss')
    ]

    # 7. Training
    print("\nStarting Training...")
    history = model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=100,
        batch_size=16,
        class_weight=class_weight_dict,
        callbacks=callbacks,
        verbose=1
    )

    # Save training history
    with open(os.path.join(results_dir, "training_history.json"), "w") as f:
        json.dump(history.history, f, indent=2)

    # 8. Evaluation
    print("\nEvaluating on Test Set...")
    test_loss, test_acc = model.evaluate(X_test, y_test, verbose=0)
    
    y_pred_probs = model.predict(X_test)
    y_pred = np.argmax(y_pred_probs, axis=1)

    # Metrics
    target_names = [reverse_label_map[i] for i in range(num_classes)]
    report_dict = classification_report(y_test, y_pred, target_names=target_names, output_dict=True)
    with open(os.path.join(results_dir, "classification_report.json"), "w") as f:
        json.dump(report_dict, f, indent=2)

    cm = confusion_matrix(y_test, y_pred)
    np.save(os.path.join(results_dir, "confusion_matrix.npy"), cm)

    # 9. Top 5 Confused Classes
    print("\n--- Top 5 Confused Class Pairs ---")
    confusions = []
    for i in range(num_classes):
        for j in range(num_classes):
            if i != j and cm[i, j] > 0:
                confusions.append((cm[i, j], target_names[i], target_names[j]))
    
    # Sort descending by count
    confusions.sort(key=lambda x: x[0], reverse=True)
    top_5 = confusions[:5]
    if not top_5:
        print("No confusions! Perfect accuracy.")
    else:
        for count, true_label, pred_label in top_5:
            print(f"{true_label} <-> {pred_label} : {count} errors")

    # 10. Visualization
    # Plot Training Accuracy
    plt.figure(figsize=(8, 6))
    plt.plot(history.history['accuracy'], label='Train Accuracy')
    plt.plot(history.history['val_accuracy'], label='Validation Accuracy')
    plt.title('Model Accuracy')
    plt.ylabel('Accuracy')
    plt.xlabel('Epoch')
    plt.legend()
    plt.savefig(os.path.join(results_dir, "training_accuracy.png"))
    plt.close()

    # Plot Training Loss
    plt.figure(figsize=(8, 6))
    plt.plot(history.history['loss'], label='Train Loss')
    plt.plot(history.history['val_loss'], label='Validation Loss')
    plt.title('Model Loss')
    plt.ylabel('Loss')
    plt.xlabel('Epoch')
    plt.legend()
    plt.savefig(os.path.join(results_dir, "training_loss.png"))
    plt.close()

    # Plot Confusion Matrix
    plt.figure(figsize=(10, 8))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=target_names, yticklabels=target_names)
    plt.title('Confusion Matrix')
    plt.ylabel('True Label')
    plt.xlabel('Predicted Label')
    plt.tight_layout()
    plt.savefig(os.path.join(results_dir, "confusion_matrix.png"))
    plt.close()

    # 11. Summary
    train_acc = history.history['accuracy'][-1]
    val_acc = history.history['val_accuracy'][-1]
    
    print("\n=== Training Summary ===")
    print(f"Dataset Size: {X.shape[0]}")
    print(f"Train/Val/Test: {len(idx_train)} / {len(idx_val)} / {len(idx_test)}")
    print(f"Train Accuracy: {train_acc:.4f}")
    print(f"Validation Accuracy: {val_acc:.4f}")
    print(f"Test Accuracy: {test_acc:.4f}")
    print("\nPer-class Performance (Test Set):")
    for name in target_names:
        class_metrics = report_dict.get(name, {})
        f1 = class_metrics.get('f1-score', 0)
        print(f"  {name}: F1-Score = {f1:.4f}")
    print("========================\n")

if __name__ == "__main__":
    main()
