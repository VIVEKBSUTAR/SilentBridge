import serial
import serial.tools.list_ports
import json
import time
import random
from config import MOCK_MODE

class SerialReader:
    def __init__(self, baud_rate=115200, default_port=None):
        self.baud_rate = baud_rate
        self.port = default_port
        self.serial_conn = None
        self.connected = False
        
        # Diagnostics
        self.diag_total_lines = 0
        self.diag_valid_json = 0
        self.diag_rejected = 0
        self.diag_first_raw = None
        self.diag_first_packet = None

    def auto_detect_port(self):
        """Scan available ports and try to find an ESP32."""
        ports = list(serial.tools.list_ports.comports())
        if not ports:
            print("No COM ports found!")
            return None
            
        print("Available COM ports:")
        for idx, p in enumerate(ports):
            print(f"[{idx}] {p.device} - {p.description}")
            
        # Categorize ports
        usb_ports = []
        bt_ports = []
        
        for p in ports:
            desc = p.description.lower()
            if "cp210" in desc or "ch340" in desc or "usb serial" in desc or "usb-to-uart" in desc:
                usb_ports.append(p)
            elif "bluetooth" in desc:
                bt_ports.append(p)
                
        # Auto-detect logic
        if len(usb_ports) == 1 and len(bt_ports) == 0:
            print(f"Auto-detected ESP32 USB on port {usb_ports[0].device}")
            return usb_ports[0].device
            
        if len(usb_ports) == 0 and len(bt_ports) == 1:
            print(f"Auto-detected ESP32 Bluetooth on port {bt_ports[0].device}")
            return bt_ports[0].device
            
        if len(usb_ports) > 0 or len(bt_ports) > 0:
            print("Multiple candidate ports found. Please select manually.")
            
        # Fallback to manual selection
        try:
            choice = int(input("Enter the number of the port to use: "))
            if 0 <= choice < len(ports):
                return ports[choice].device
        except ValueError:
            pass
            
        print("Invalid selection.")
        return None

    def connect(self):
        """Establish connection to the serial port."""
        if MOCK_MODE:
            self.connected = True
            print("MOCK MODE ENABLED. Generating fake data.")
            return True
            
        if self.port is None:
            self.port = self.auto_detect_port()
            
        if not self.port:
            return False
            
        try:
            self.serial_conn = serial.Serial(self.port, self.baud_rate, timeout=1)
            self.connected = True
            print(f"Connected to {self.port} at {self.baud_rate} baud.")
            time.sleep(2) # Wait for ESP32 to reset if it resets on connect
            self.serial_conn.reset_input_buffer()
            return True
        except serial.SerialException as e:
            print(f"Failed to connect to {self.port}: {e}")
            return False

    def disconnect(self):
        """Close the connection."""
        print("\n--- Diagnostics Summary ---")
        print(f"Total lines read: {self.diag_total_lines}")
        print(f"Valid JSON packets: {self.diag_valid_json}")
        print(f"Rejected lines: {self.diag_rejected}")
        
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
        self.connected = False
        print("Disconnected from serial port.")

    def read_json_packet(self):
        """Read a single line from serial and parse it as JSON."""
        if not self.connected:
            return None
            
        if MOCK_MODE:
            time.sleep(0.02) # Simulate 50Hz
            return {
                "timestamp": int(time.time() * 1000),
                "thumb": random.randint(1500, 3000),
                "index": random.randint(1500, 3000),
                "middle": random.randint(1500, 3000),
                "ring": random.randint(1500, 3000),
                "little": random.randint(1500, 3000),
                "ax": round(random.uniform(-1, 1), 2),
                "ay": round(random.uniform(-1, 1), 2),
                "az": round(random.uniform(8, 10), 2),
                "gx": round(random.uniform(-10, 10), 2),
                "gy": round(random.uniform(-10, 10), 2),
                "gz": round(random.uniform(-10, 10), 2),
                "pitch": round(random.uniform(-20, 20), 2),
                "roll": round(random.uniform(-20, 20), 2)
            }
            
        if not self.serial_conn:
            return None
            
        try:
            if self.serial_conn.in_waiting > 0:
                raw_line = self.serial_conn.readline()
                self.diag_total_lines += 1
                
                if self.diag_first_raw is None:
                    self.diag_first_raw = raw_line
                    print(f"\n[DIAGNOSTIC] First raw byte string received: {raw_line}")
                    
                line = raw_line.decode('utf-8', errors='ignore').strip()
                if not line:
                    self.diag_rejected += 1
                    return None
                    
                try:
                    packet = json.loads(line)
                    self.diag_valid_json += 1
                    
                    if self.diag_first_packet is None:
                        self.diag_first_packet = packet
                        print(f"\n[DIAGNOSTIC] First parsed JSON packet: {packet}")
                        
                    return packet
                except json.JSONDecodeError:
                    self.diag_rejected += 1
                    if self.diag_rejected == 1:
                        print(f"\n[DIAGNOSTIC] First rejected line (invalid JSON): '{line}'")
                    # Ignore invalid JSON, could be partial read or noise
                    return None
        except serial.SerialException as e:
            print(f"\nSerial error (device disconnected?): {e}")
            self.connected = False
            return None
            
        return None
