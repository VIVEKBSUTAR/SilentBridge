"""
SilentBridge — Real-Time Inference (Manual Start/Stop Flow)

State machine:
  READY        → user presses [Start]
  CALIBRATING  → 3 s of stillness, sets gyro threshold
  IDLE         → waiting for motion above threshold (one gesture allowed)
  RECORDING    → capturing frames until motion settles
  RESULT       → shows prediction; waits for [Stop] to reset to READY
"""

import os
import sys
import time
import json
import numpy as np
import threading
import tkinter as tk
from tkinter import font as tkfont
import joblib
import tensorflow as tf

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import BASE_DIR, PROCESSED_DATA_DIR, SCALERS_DIR, FEATURES, MPU_FEATURES, FEATURE_COUNT

sys.path.append(BASE_DIR)
from dataset_tools.serial_reader import SerialReader
from ml.src.normalizer import Normalizer
from ml.src.resampler import Resampler
from ml.src.feature_extractor import FeatureExtractor

# ── State constants ─────────────────────────────────────────────────────────
STATE_READY       = "READY"
STATE_CALIBRATING = "CALIBRATING"
STATE_IDLE        = "IDLE"
STATE_RECORDING   = "RECORDING"
STATE_RESULT      = "RESULT"

# ── Tuning ───────────────────────────────────────────────────────────────────
CALIBRATION_SECS    = 3      # seconds of stillness to measure noise
GYRO_MARGIN         = 15.0   # added on top of max noise reading
IDLE_SETTLE_FRAMES  = 15     # 300 ms of quiet = gesture ended
MIN_GESTURE_FRAMES  = 15     # ignore micro-twitches shorter than this
CONFIDENCE_THRESHOLD = 0.90  # reject predictions below this


class RealtimeInferenceApp:
    # ── Init ────────────────────────────────────────────────────────────────
    def __init__(self, root):
        self.root = root
        self.root.title("SilentBridge — Real-Time Inference")
        self.root.geometry("640x480")
        self.root.configure(bg="#1e1e2e")
        self.root.resizable(False, False)

        self._load_ml_assets()
        self._init_state()
        self._build_ui()

        self.reader = SerialReader()

        # Serial runs in background; only active when user presses Start
        self.serial_thread = None
        self.running = False

        # UI refreshes on the main thread
        self.root.after(80, self._tick_ui)

    def _load_ml_assets(self):
        print("Loading ML assets…")
        model_path      = os.path.join(BASE_DIR, "ml", "models", "best_model.keras")
        scaler_path     = os.path.join(SCALERS_DIR, "feature_scaler.pkl")
        label_map_path  = os.path.join(PROCESSED_DATA_DIR, "label_map.json")

        self.model  = tf.keras.models.load_model(model_path)
        self.scaler = joblib.load(scaler_path)

        with open(label_map_path) as f:
            label_map = json.load(f)
        self.target_names = [k for k, v in sorted(label_map.items(), key=lambda x: x[1])]

        self.normalizer   = Normalizer()
        self.resampler    = Resampler()
        self.mpu_indices  = [FEATURES.index(f) for f in MPU_FEATURES]
        print("ML assets loaded.")

    def _init_state(self):
        self.state             = STATE_READY
        self.calibrating_frames = []
        self.recording_frames  = []
        self.gyro_threshold    = 20.0
        self.idle_counter      = 0

        # Thread-safe display queue (written by serial thread, read by UI tick)
        self._ui = {
            "conn":    ("Not connected", "gray"),
            "state":   (STATE_READY, "white"),
            "gesture": ("---", "#a6e3a1"),
            "conf":    ("Confidence: —", "white"),
        }

    # ── UI ──────────────────────────────────────────────────────────────────
    def _build_ui(self):
        BG = "#1e1e2e"

        font_sm  = tkfont.Font(family="Helvetica", size=13, weight="bold")
        font_lg  = tkfont.Font(family="Helvetica", size=52, weight="bold")
        font_btn = tkfont.Font(family="Helvetica", size=14, weight="bold")

        # Connection status
        self.lbl_conn = tk.Label(self.root, text="Not connected",
                                 fg="gray", bg=BG, font=font_sm)
        self.lbl_conn.pack(pady=(18, 2))

        # State indicator
        self.lbl_state = tk.Label(self.root, text=STATE_READY,
                                  fg="white", bg=BG, font=font_sm)
        self.lbl_state.pack(pady=2)

        # Big gesture display
        self.lbl_gesture = tk.Label(self.root, text="---",
                                    fg="#a6e3a1", bg=BG, font=font_lg)
        self.lbl_gesture.pack(expand=True)

        # Confidence
        self.lbl_conf = tk.Label(self.root, text="Confidence: —",
                                 fg="white", bg=BG, font=font_sm)
        self.lbl_conf.pack(pady=(0, 14))

        # Button row
        btn_frame = tk.Frame(self.root, bg=BG)
        btn_frame.pack(pady=(0, 24))

        self.btn_start = tk.Button(
            btn_frame, text="▶  Start",
            command=self._on_start,
            font=font_btn,
            bg="#40a02b", fg="white", activebackground="#2d7a1f",
            relief="flat", padx=24, pady=10, cursor="hand2"
        )
        self.btn_start.grid(row=0, column=0, padx=12)

        self.btn_stop = tk.Button(
            btn_frame, text="■  Stop",
            command=self._on_stop,
            font=font_btn,
            bg="#e64553", fg="white", activebackground="#b03040",
            relief="flat", padx=24, pady=10, cursor="hand2",
            state=tk.DISABLED
        )
        self.btn_stop.grid(row=0, column=1, padx=12)

    def _tick_ui(self):
        """Apply buffered updates from the serial thread (runs on main thread)."""
        ui = self._ui
        self.lbl_conn.config(text=ui["conn"][0],    fg=ui["conn"][1])
        self.lbl_state.config(text=ui["state"][0],  fg=ui["state"][1])
        self.lbl_gesture.config(text=ui["gesture"][0], fg=ui["gesture"][1])
        self.lbl_conf.config(text=ui["conf"][0],    fg=ui["conf"][1])
        self.root.after(80, self._tick_ui)

    def _set_ui(self, **kwargs):
        """Thread-safe UI update (call from serial thread)."""
        self._ui.update(kwargs)

    # ── Button handlers ─────────────────────────────────────────────────────
    def _on_start(self):
        """Start button: connect (if needed) and kick off one calibrate→sign cycle."""
        self.btn_start.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.NORMAL)

        # Reset display
        self._set_ui(
            gesture=("---", "#a6e3a1"),
            conf=("Confidence: —", "white"),
        )

        # First ever press: connect and launch the serial thread
        if self.serial_thread is None or not self.serial_thread.is_alive():
            self.running = True
            self.serial_thread = threading.Thread(target=self._serial_loop, daemon=True)
            self.serial_thread.start()
        else:
            # Already connected — just kick off a fresh calibration cycle
            # (thread keeps running; BT/COM port unchanged)
            self._begin_calibration()

    def _on_stop(self):
        """Stop button: reset state to READY without touching the connection."""
        self.state = STATE_READY

        self._set_ui(
            state=(STATE_READY, "white"),
            gesture=("---", "#a6e3a1"),
            conf=("Confidence: —", "white"),
        )
        self.btn_start.config(state=tk.NORMAL)
        self.btn_stop.config(state=tk.DISABLED)
        # Connection and serial thread stay alive — no disconnect, no COM prompt

    # ── Serial thread ────────────────────────────────────────────────────────
    def _serial_loop(self):
        # Connect
        if not self.reader.connect():
            self._set_ui(conn=("Connection failed", "red"),
                         state=(STATE_READY, "white"))
            self.root.after(0, lambda: (
                self.btn_start.config(state=tk.NORMAL),
                self.btn_stop.config(state=tk.DISABLED),
            ))
            return

        self._set_ui(conn=("Connected", "#a6e3a1"))
        self._begin_calibration()

        while self.running and self.reader.connected:
            # In READY or RESULT states just drain the buffer quietly
            if self.state in (STATE_READY, STATE_RESULT):
                self.reader.read_json_packet()  # discard
                time.sleep(0.005)
                continue

            packet = self.reader.read_json_packet()
            if not packet:
                time.sleep(0.005)
                continue

            gx = packet.get("gx", 0)
            gy = packet.get("gy", 0)
            gz = packet.get("gz", 0)
            gyro_mag = float(np.sqrt(gx**2 + gy**2 + gz**2))

            if self.state == STATE_CALIBRATING:
                self._handle_calibrating(gyro_mag)

            elif self.state == STATE_IDLE:
                self._handle_idle(packet, gyro_mag)

            elif self.state == STATE_RECORDING:
                self._handle_recording(packet, gyro_mag)
            # STATE_RESULT / STATE_READY: handled above by drain branch

    # ── State handlers ───────────────────────────────────────────────────────
    def _begin_calibration(self):
        self.state              = STATE_CALIBRATING
        self.calibrating_frames = []
        self.recording_frames   = []
        self.idle_counter       = 0
        self._calib_start       = time.time()

        self._set_ui(state=("Hold still… calibrating", "#f9e2af"))
        print("Calibration started.")

    def _handle_calibrating(self, gyro_mag):
        self.calibrating_frames.append(gyro_mag)

        elapsed = time.time() - self._calib_start
        remaining = max(0, CALIBRATION_SECS - elapsed)
        self._set_ui(state=(f"Hold still… {remaining:.1f}s", "#f9e2af"))

        if elapsed >= CALIBRATION_SECS:
            noise_max         = max(self.calibrating_frames) if self.calibrating_frames else 0.0
            self.gyro_threshold = noise_max + GYRO_MARGIN
            print(f"Calibration done. Noise max={noise_max:.2f}, threshold={self.gyro_threshold:.2f}")

            self._set_ui(state=("Calibrated — do your gesture", "#a6e3a1"))
            time.sleep(0.8)  # brief visual confirmation

            self.state = STATE_IDLE
            self._set_ui(state=("Waiting for gesture…", "white"))

    def _handle_idle(self, packet, gyro_mag):
        if gyro_mag > self.gyro_threshold:
            self.state          = STATE_RECORDING
            self.recording_frames = [packet]
            self.idle_counter   = 0
            self._set_ui(state=("Recording…", "#f38ba8"),
                         gesture=("…", "#f38ba8"),
                         conf=("Confidence: —", "white"))
            print("Gesture started.")

    def _handle_recording(self, packet, gyro_mag):
        self.recording_frames.append(packet)

        if gyro_mag < self.gyro_threshold:
            self.idle_counter += 1
        else:
            self.idle_counter = 0

        if self.idle_counter >= IDLE_SETTLE_FRAMES:
            # Trim the trailing quiet tail
            valid_frames = self.recording_frames[:-IDLE_SETTLE_FRAMES]
            print(f"Gesture ended. {len(valid_frames)} frames captured.")

            self.state = STATE_RESULT
            self._set_ui(state=("Classifying…", "#89b4fa"))
            self._classify(valid_frames)
            # Stay in STATE_RESULT; serial loop drains quietly
            # User must press Stop to reset

    # ── Inference ────────────────────────────────────────────────────────────
    def _classify(self, frames):
        if len(frames) < MIN_GESTURE_FRAMES:
            self._set_ui(
                state=("Too short — press Stop and try again", "gray"),
                gesture=("---", "gray"),
                conf=("Confidence: —", "white"),
            )
            return

        # 1. Extract (N, 13)
        raw = FeatureExtractor.extract({"frames": frames})

        # 2. Normalise Hall sensors
        normed = self.normalizer.normalize_hall_sensors(raw)

        # 3. Resample → (100, 13)
        resampled = self.resampler.resample(normed)

        # 4. Standardise IMU columns
        X = resampled.copy()
        X[:, self.mpu_indices] = self.scaler.transform(X[:, self.mpu_indices])

        # 5. Predict
        X_in  = np.expand_dims(X, axis=0)          # (1, 100, 13)
        probs = self.model.predict(X_in, verbose=0)[0]

        best_idx   = int(np.argmax(probs))
        confidence = float(probs[best_idx])
        gesture    = self.target_names[best_idx]

        duration = len(frames) * 0.02
        print(f"Prediction: {gesture}  conf={confidence:.3f}  dur={duration:.2f}s")

        if confidence >= CONFIDENCE_THRESHOLD:
            self._set_ui(
                state=("Done — press Stop to reset", "#a6e3a1"),
                gesture=(gesture, "#a6e3a1"),
                conf=(f"Confidence: {confidence*100:.1f}%", "white"),
            )
        else:
            # Show the best guess but flag it as low confidence
            self._set_ui(
                state=("Low confidence — press Stop and try again", "#fab387"),
                gesture=(gesture, "#fab387"),
                conf=(f"Low confidence: {confidence*100:.1f}%", "#fab387"),
            )

    # ── Cleanup ──────────────────────────────────────────────────────────────
    def on_closing(self):
        self.running = False
        try:
            self.reader.disconnect()
        except Exception:
            pass
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app  = RealtimeInferenceApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()