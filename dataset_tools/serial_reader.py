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

    def auto_detect_port(self):
        """Scan available ports and try to find an ESP32."""
        ports = list(serial.tools.list_ports.comports())
        if not ports:
            print("No COM ports found!")
            return None
            
        print("Available COM ports:")
        for idx, p in enumerate(ports):
            print(f"[{idx}] {p.device} - {p.description}")
            
        # Very basic heuristic: CP210x or CH340 are common ESP32 USB-UART bridges
        for p in ports:
            desc = p.description.lower()
            if "cp210" in desc or "ch340" in desc or "serial" in desc:
                print(f"Auto-detected likely ESP32 on port {p.device}")
                return p.device
                
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
                line = self.serial_conn.readline().decode('utf-8', errors='ignore').strip()
                if not line:
                    return None
                    
                try:
                    packet = json.loads(line)
                    return packet
                except json.JSONDecodeError:
                    # Ignore invalid JSON, could be partial read or noise
                    return None
        except serial.SerialException as e:
            print(f"\nSerial error (device disconnected?): {e}")
            self.connected = False
            return None
            
        return None
