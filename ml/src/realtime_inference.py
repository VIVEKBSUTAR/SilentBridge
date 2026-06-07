import os
import sys
import time
import json
import numpy as np
import threading
import tkinter as tk
from tkinter import font
import joblib
import tensorflow as tf

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import BASE_DIR, PROCESSED_DATA_DIR, SCALERS_DIR, FEATURES, MPU_FEATURES, FEATURE_COUNT
sys.path.append(BASE_DIR)
from dataset_tools.serial_reader import SerialReader
from ml.src.normalizer import Normalizer
from ml.src.resampler import Resampler
from ml.src.feature_extractor import FeatureExtractor

class RealtimeInferenceApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SilentBridge - Real-Time Inference")
        self.root.geometry("600x400")
        self.root.configure(bg="#1e1e2e")
        
        # Load ML Assets
        self.load_ml_assets()
        
        # State
        self.state = "INIT"
        self.calibrating_frames = []
        self.recording_frames = []
        self.idle_counter = 0
        self.gyro_threshold = 20.0 # Default fallback
        
        # UI Setup
        self.setup_ui()
        
        # Serial Setup
        self.reader = SerialReader()
        
        # Start background thread
        self.running = True
        self.thread = threading.Thread(target=self.serial_loop)
        self.thread.daemon = True
        self.thread.start()
        
        # Periodic UI update check (runs on main thread)
        self.root.after(100, self.update_ui)
        
    def load_ml_assets(self):
        print("Loading ML Assets...")
        model_path = os.path.join(BASE_DIR, "ml", "models", "best_model.keras")
        scaler_path = os.path.join(SCALERS_DIR, "feature_scaler.pkl")
        label_map_path = os.path.join(PROCESSED_DATA_DIR, "label_map.json")
        
        self.model = tf.keras.models.load_model(model_path)
        self.scaler = joblib.load(scaler_path)
        with open(label_map_path, "r") as f:
            label_map = json.load(f)
        self.target_names = [k for k, v in sorted(label_map.items(), key=lambda item: item[1])]
        
        self.normalizer = Normalizer()
        self.resampler = Resampler()
        self.mpu_indices = [FEATURES.index(f) for f in MPU_FEATURES]
        print("ML Assets Loaded Successfully.")
        
    def setup_ui(self):
        custom_font = font.Font(family="Helvetica", size=16, weight="bold")
        large_font = font.Font(family="Helvetica", size=48, weight="bold")
        
        self.conn_label = tk.Label(self.root, text="Connecting...", fg="orange", bg="#1e1e2e", font=custom_font)
        self.conn_label.pack(pady=10)
        
        self.state_label = tk.Label(self.root, text="State: INIT", fg="white", bg="#1e1e2e", font=custom_font)
        self.state_label.pack(pady=10)
        
        self.gesture_label = tk.Label(self.root, text="---", fg="#a6e3a1", bg="#1e1e2e", font=large_font)
        self.gesture_label.pack(expand=True)
        
        self.conf_label = tk.Label(self.root, text="Confidence: 0.00%", fg="white", bg="#1e1e2e", font=custom_font)
        self.conf_label.pack(pady=20)
        
        # Thread-safe UI update queues
        self.ui_update_conn = "Connecting..."
        self.ui_update_conn_color = "orange"
        self.ui_update_state = "State: INIT"
        self.ui_update_state_color = "white"
        self.ui_update_gesture = "---"
        self.ui_update_conf = "Confidence: 0.00%"
        
    def update_ui(self):
        self.conn_label.config(text=self.ui_update_conn, fg=self.ui_update_conn_color)
        self.state_label.config(text=self.ui_update_state, fg=self.ui_update_state_color)
        self.gesture_label.config(text=self.ui_update_gesture)
        self.conf_label.config(text=self.ui_update_conf)
        self.root.after(100, self.update_ui)
        
    def serial_loop(self):
        if not self.reader.connect():
            self.ui_update_conn = "Disconnected"
            self.ui_update_conn_color = "red"
            return
            
        self.ui_update_conn = "Connected"
        self.ui_update_conn_color = "#a6e3a1"
        self.state = "CALIBRATING"
        self.ui_update_state = "Calibrating (Keep hand still)..."
        self.ui_update_state_color = "yellow"
        
        calibration_start = time.time()
        
        while self.running and self.reader.connected:
            packet = self.reader.read_json_packet()
            if not packet:
                continue
                
            # Compute gyro mag
            gx = packet.get("gx", 0)
            gy = packet.get("gy", 0)
            gz = packet.get("gz", 0)
            gyro_mag = np.sqrt(gx**2 + gy**2 + gz**2)
            
            if self.state == "CALIBRATING":
                self.calibrating_frames.append(gyro_mag)
                if time.time() - calibration_start >= 3.0:
                    # Calibration complete
                    if self.calibrating_frames:
                        # Baseline noise max + 15 units margin
                        self.gyro_threshold = max(self.calibrating_frames) + 15.0
                    print(f"Calibration Complete. Gyro Threshold set to: {self.gyro_threshold:.2f}")
                    self.ui_update_state = "Calibration Complete"
                    self.ui_update_state_color = "#a6e3a1"
                    time.sleep(1) # Show complete briefly
                    self.state = "IDLE"
                    self.ui_update_state = "IDLE"
                    self.ui_update_state_color = "white"
            
            elif self.state == "IDLE":
                if gyro_mag > self.gyro_threshold:
                    self.state = "RECORDING"
                    self.ui_update_state = "RECORDING..."
                    self.ui_update_state_color = "#f38ba8"
                    self.recording_frames = [packet]
                    self.idle_counter = 0
                    
            elif self.state == "RECORDING":
                self.recording_frames.append(packet)
                if gyro_mag < self.gyro_threshold:
                    self.idle_counter += 1
                else:
                    self.idle_counter = 0
                    
                if self.idle_counter >= 15: # 300ms timeout of resting
                    # Gesture Ended
                    valid_frames = self.recording_frames[:-15]
                    self.process_gesture(valid_frames)
                    
                    self.state = "IDLE"
                    self.ui_update_state = "IDLE"
                    self.ui_update_state_color = "white"
                    self.recording_frames = []
                    
    def process_gesture(self, frames):
        if len(frames) < 15: # Skip micro twitches
            return
            
        # 1. Feature Extraction
        dict_rec = {"frames": frames}
        features_2d = FeatureExtractor.extract(dict_rec)
        
        # 2. Normalize Hall Sensors
        norm_features = self.normalizer.normalize_hall_sensors(features_2d)
        
        # 3. Resample
        resampled_features = self.resampler.resample(norm_features)
        
        # 4. Standardize MPU
        X_2d = resampled_features.copy()
        mpu_data = X_2d[:, self.mpu_indices]
        mpu_scaled = self.scaler.transform(mpu_data)
        X_2d[:, self.mpu_indices] = mpu_scaled
        
        # 5. Inference
        X_tensor = np.expand_dims(X_2d, axis=0) # (1, 100, 13)
        preds = self.model.predict(X_tensor, verbose=0)[0]
        
        best_idx = np.argmax(preds)
        confidence = preds[best_idx]
        gesture = self.target_names[best_idx]
        
        # Calculate diagnostics
        max_gyro = 0
        for f in frames:
            g = np.sqrt(f.get("gx",0)**2 + f.get("gy",0)**2 + f.get("gz",0)**2)
            if g > max_gyro:
                max_gyro = g
                
        duration = len(frames) * 0.02 # 50Hz = 20ms per frame
        
        print(f"\n--- Segmentation Diagnostics ---")
        print(f"Captured Frames: {len(frames)}")
        print(f"Gesture Duration: {duration:.2f}s")
        print(f"Max Gyro Magnitude: {max_gyro:.2f}")
        print(f"Prediction: {gesture} (Conf: {confidence:.4f})")
        
        if confidence > 0.90:
            self.ui_update_gesture = gesture
            self.ui_update_conf = f"Confidence: {confidence*100:.1f}%"
        else:
            self.ui_update_conf = f"Low Confidence: {confidence*100:.1f}% (Rejected)"
            
    def on_closing(self):
        self.running = False
        if hasattr(self, 'reader'):
            self.reader.disconnect()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = RealtimeInferenceApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
