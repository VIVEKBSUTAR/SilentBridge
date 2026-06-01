import sys
import threading
import time
from config import BAUD_RATE, DEFAULT_COM_PORT, SUPPORTED_LABELS
from serial_reader import SerialReader
from dataset_manager import save_recording

# Global state for the background reading thread
is_recording = False
frame_buffer = []
buffer_lock = threading.Lock()

def serial_read_worker(reader):
    global is_recording, frame_buffer
    while reader.connected:
        packet = reader.read_json_packet()
        if packet:
            with buffer_lock:
                if is_recording:
                    frame_buffer.append(packet)
        # Small sleep to prevent tight looping when no data
        time.sleep(0.005)

def main():
    print("--- SilentBridge Dataset Collector ---")
    reader = SerialReader(baud_rate=BAUD_RATE, default_port=DEFAULT_COM_PORT)
    
    if not reader.connect():
        print("Failed to initialize Serial Reader. Exiting.")
        sys.exit(1)
        
    # Start background reading thread
    reader_thread = threading.Thread(target=serial_read_worker, args=(reader,), daemon=True)
    reader_thread.start()
    
    try:
        while True:
            print("\n" + "-"*40)
            print("Supported Labels:")
            print(", ".join(SUPPORTED_LABELS))
            
            label = input("\nEnter Gesture Label (or 'q' to quit): ").strip().upper()
            
            if label == 'Q':
                break
                
            if label not in SUPPORTED_LABELS:
                print(f"Error: '{label}' is not in the supported labels list.")
                continue
                
            print("\nReady To Record")
            input("Press ENTER To Start...")
            
            # Start recording
            global is_recording, frame_buffer
            with buffer_lock:
                frame_buffer = []
                is_recording = True
                
            print("\nRecording Started")
            print("Frames Collected: 0 (Press ENTER to stop)", end="\r")
            
            # Main thread waits for user to press ENTER again to stop
            # We can run a small loop to update the frame count display
            stop_event = threading.Event()
            
            def wait_for_enter():
                input()
                stop_event.set()
                
            input_thread = threading.Thread(target=wait_for_enter, daemon=True)
            input_thread.start()
            
            while not stop_event.is_set():
                with buffer_lock:
                    count = len(frame_buffer)
                print(f"Frames Collected: {count} (Press ENTER to stop)    ", end="\r")
                time.sleep(0.1)
                
            # Stop recording
            with buffer_lock:
                is_recording = False
                captured_frames = list(frame_buffer)
                
            print(f"\n\nRecording Finished")
            print(f"Frames Captured: {len(captured_frames)}")
            print("Saving File...")
            
            if len(captured_frames) == 0:
                print("Error: No frames were captured. Discarding recording.")
                continue
                
            try:
                filepath = save_recording(label, captured_frames)
                print(f"Success! Saved to {filepath}")
            except Exception as e:
                print(f"Error saving recording: {e}")
                
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        reader.disconnect()

if __name__ == "__main__":
    main()
