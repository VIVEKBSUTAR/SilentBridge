"""
SilentBridge — Dataset Collector (v2, Multi-User)

Changes from v1:
  - Asks for a User ID at startup (or auto-assigns next available user_XXX)
  - Saves recordings under data/raw/user_XXX/LABEL/LABEL_NNNN.json
  - Performs a 2-step sensor calibration (open hand → fist) before recording
  - Calibration is saved to data/calibration/user_XXX_calibration.json
  - All other UX is identical to v1

Usage:
    python collector.py              # interactive mode (asks for user ID)
    python collector.py --user 007   # specify user directly
    python collector.py --mock       # run without hardware
"""

import sys
import os
import threading
import time
import json
import argparse

from config import BAUD_RATE, DEFAULT_COM_PORT
from serial_reader import SerialReader
from dataset_manager import save_recording

# ── Global recording state ──────────────────────────────────────────────────
is_recording = False
frame_buffer = []
buffer_lock  = threading.Lock()


def serial_read_worker(reader):
    global is_recording, frame_buffer
    while reader.connected:
        packet = reader.read_json_packet()
        if packet:
            with buffer_lock:
                if is_recording:
                    frame_buffer.append(packet)
        time.sleep(0.005)


# ── User ID management ──────────────────────────────────────────────────────
def resolve_user_id(raw_dir, requested_id=None):
    """
    If the caller supplied a user ID, validate/format it.
    Otherwise scan the raw_dir and return the next available user_XXX id.
    """
    if requested_id:
        uid = requested_id.strip()
        if not uid.startswith("user_"):
            uid = f"user_{uid.zfill(3)}"
        return uid

    # Auto-assign
    existing = []
    if os.path.exists(raw_dir):
        existing = [
            d for d in os.listdir(raw_dir)
            if d.startswith("user_") and os.path.isdir(os.path.join(raw_dir, d))
        ]
    if not existing:
        return "user_001"
    nums = []
    for e in existing:
        try:
            nums.append(int(e.split("_")[1]))
        except (IndexError, ValueError):
            pass
    next_num = (max(nums) + 1) if nums else 1
    return f"user_{str(next_num).zfill(3)}"


# ── Sensor calibration ───────────────────────────────────────────────────────
def run_sensor_calibration(reader, calib_dir, user_id, calib_secs=3):
    """
    Runs open-hand and closed-fist calibration.
    Saves results to data/calibration/user_XXX_calibration.json.
    Returns (open_values, closed_values) dicts.
    """
    FINGERS = ["thumb", "index", "middle", "ring", "little"]

    def collect_readings(label, secs=calib_secs):
        print(f"\n  → {label}")
        print(f"     Hold this position for {secs} seconds…")
        time.sleep(0.5)

        samples = {f: [] for f in FINGERS}
        t_end = time.time() + secs
        while time.time() < t_end:
            pkt = reader.read_json_packet()
            if pkt and isinstance(pkt, dict):
                for f in FINGERS:
                    if f in pkt:
                        samples[f].append(pkt[f])
            time.sleep(0.015)

        import numpy as np
        result = {}
        for f in FINGERS:
            if samples[f]:
                result[f] = float(np.median(samples[f]))
            else:
                print(f"  [WARN] No data for {f}, defaulting to 2048")
                result[f] = 2048.0
        print(f"     Done. Values: { {f: round(result[f]) for f in FINGERS} }")
        return result

    print("\n" + "="*50)
    print("SENSOR CALIBRATION")
    print("="*50)
    input("  Press ENTER, then open your hand fully (relax all fingers)…")
    open_vals = collect_readings("OPEN HAND")

    input("  Press ENTER, then make a tight fist…")
    closed_vals = collect_readings("CLOSED FIST")

    # Save
    os.makedirs(calib_dir, exist_ok=True)
    calib_path = os.path.join(calib_dir, f"{user_id}_calibration.json")
    cal_data = {
        "user_id": user_id,
        "open":    open_vals,
        "closed":  closed_vals,
        "recorded_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    with open(calib_path, "w") as f:
        json.dump(cal_data, f, indent=2)
    print(f"\n  Calibration saved → {calib_path}")
    return open_vals, closed_vals


# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    p = argparse.ArgumentParser(description="SilentBridge Dataset Collector v2")
    p.add_argument("--user",   default=None, help="User ID (e.g. 001 or user_001). Omit to save flat to data/raw/LABEL/")
    p.add_argument("--mock",   action="store_true", help="Run in mock mode (no hardware)")
    p.add_argument("--no-calib", action="store_true",
                   help="Skip sensor calibration step")
    args = p.parse_args()

    # Paths
    base_dir  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    raw_dir   = os.path.join(base_dir, "data", "raw")
    calib_dir = os.path.join(base_dir, "data", "calibration")

    user_id = None
    print(f"\n--- SilentBridge Dataset Collector ---")
    if args.user:
        user_id = resolve_user_id(raw_dir, args.user)
        print(f"User ID: {user_id}  →  data/raw/{user_id}/LABEL/")
    else:
        user_id = None
        print(f"User ID: none  →  data/raw/LABEL/  (flat layout)")

    # Connect
    if args.mock:
        os.environ["SILENTBRIDGE_MOCK"] = "1"   # SerialReader checks this
    reader = SerialReader(baud_rate=BAUD_RATE, default_port=DEFAULT_COM_PORT)
    if not reader.connect():
        print("Failed to connect. Exiting.")
        sys.exit(1)

    # Background read thread
    reader_thread = threading.Thread(target=serial_read_worker, args=(reader,), daemon=True)
    reader_thread.start()

    # Sensor calibration
    if not args.no_calib:
        run_sensor_calibration(reader, calib_dir, user_id)
    else:
        print("Skipping sensor calibration.")

    # Recording loop
    global is_recording, frame_buffer
    try:
        while True:
            print("\n" + "-"*40)
            print(f"Collecting for: {user_id}")

            # Show existing labels collected so far as a hint
            user_raw_dir = os.path.join(raw_dir, user_id) if user_id else raw_dir
            if os.path.exists(user_raw_dir):
                existing_labels = sorted(os.listdir(user_raw_dir))
                if existing_labels:
                    counts = []
                    for lbl in existing_labels:
                        import glob
                        n = len(glob.glob(os.path.join(user_raw_dir, lbl, "*.json")))
                        counts.append(f"{lbl}({n})")
                    print("Existing labels: " + "  ".join(counts))

            label = input("\nEnter Gesture Label (or 'q' to quit): ").strip().upper()
            if label == "Q":
                break

            # Sanitise — only allow letters, digits and underscores
            import re
            label = re.sub(r'[^A-Z0-9_]', '_', label)
            if not label:
                print("Empty label — try again.")
                continue

            input("Press ENTER to start recording…")

            with buffer_lock:
                frame_buffer = []
                is_recording = True

            print("Recording… (Press ENTER to stop)")

            stop_event = threading.Event()

            def wait_for_enter():
                input()
                stop_event.set()

            input_thread = threading.Thread(target=wait_for_enter, daemon=True)
            input_thread.start()

            while not stop_event.is_set():
                with buffer_lock:
                    count = len(frame_buffer)
                print(f"  Frames: {count}   ", end="\r")
                time.sleep(0.1)

            with buffer_lock:
                is_recording = False
                captured = list(frame_buffer)

            print(f"\nCaptured {len(captured)} frames.")

            if not captured:
                print("No frames captured — discarding.")
                continue

            try:
                filepath = save_recording(label, captured, user_id=user_id)
                print(f"Saved → {filepath}")
            except Exception as e:
                print(f"Error saving: {e}")

    except KeyboardInterrupt:
        print("\nExiting…")
    finally:
        reader.disconnect()


if __name__ == "__main__":
    main()