# Hardware Testing Guide for SilentBridge

This guide explains how to validate the Phase 1 dataset collection pipeline once the hardware is connected.

## 1. Hardware Connections

Connect the components to your ESP32 DevKit V1 as follows:

### Hall Effect Sensors
| Finger | ESP32 GPIO |
|--------|------------|
| Thumb  | GPIO32     |
| Index  | GPIO25     |
| Middle | GPIO35     |
| Ring   | GPIO33     |
| Little | GPIO34     |

*(Ensure sensors have common VCC and GND appropriately)*

### MPU6050
| Pin | ESP32 GPIO |
|-----|------------|
| SDA | GPIO21     |
| SCL | GPIO22     |
| VCC | 3.3V       |
| GND | GND        |

## 2. Upload Firmware

1. Open Arduino IDE (or PlatformIO).
2. Install the `Adafruit MPU6050` and `Adafruit Unified Sensor` libraries.
3. Open `firmware/SilentBridge_ESP32/SilentBridge_ESP32.ino`.
4. Select your ESP32 board and the corresponding COM port.
5. Click **Upload**.
6. Do **NOT** open the Arduino Serial Monitor if you intend to run the Python script (only one program can use the COM port at a time).

## 3. Run Dataset Collector

1. Open a terminal.
2. Navigate to `dataset_tools`.
3. Install dependencies if you haven't: `pip install -r requirements.txt`
4. Run the collector: `python collector.py`

## 4. Expected Workflow & Output

1. The script will attempt to auto-detect the ESP32. If it fails, it will list COM ports (e.g., `[0] COM3 - USB-SERIAL CH340`) and ask you to enter a number.
2. It will prompt for a label:
   ```
   Enter Gesture Label (or 'q' to quit): HELLO
   ```
3. It will wait for you to press `ENTER`.
   ```
   Ready To Record
   Press ENTER To Start...
   ```
4. Once you press `ENTER`, perform the gesture. The terminal will show a live counter:
   ```
   Recording Started
   Frames Collected: 115 (Press ENTER to stop)
   ```
5. Press `ENTER` again to stop. The script validates the data and saves it.
   ```
   Recording Finished
   Frames Captured: 115
   Saving File...
   Success! Saved to c:\...\data\raw\HELLO\HELLO_0001.json
   ```

## 5. Bluetooth Wireless Collection (Optional)

The ESP32 firmware now supports Bluetooth Classic simultaneously with USB Serial.

### Pairing the ESP32
1. Power the ESP32 (via battery or USB).
2. Open **Bluetooth & devices** settings on your Windows PC.
3. Click **Add device** -> **Bluetooth**.
4. Look for **SilentBridge** and pair with it.

### Finding the Bluetooth COM Port
1. Windows automatically creates two "Standard Serial over Bluetooth link" COM ports for paired devices (one incoming, one outgoing).
2. You do not need to figure out which one is correct; the `collector.py` script will list them.

### Running Collector over Bluetooth
1. Run `python collector.py`.
2. If multiple COM ports (USB + Bluetooth) are detected, the script will ask you to select one manually.
3. Type the number corresponding to the Bluetooth COM port (try them if unsure).
4. The recording workflow remains **exactly the same**.

### Switching Back to USB
- Simply plug the USB cable back in.
- The `collector.py` script prioritizes USB ports during auto-detection if no Bluetooth ports are active, or you can manually select the USB-UART COM port.

## 6. Mock Mode Testing (Without Hardware)

If you want to test the script without an ESP32 connected:
1. Open `dataset_tools/config.py`.
2. Change `MOCK_MODE = False` to `MOCK_MODE = True`.
3. Run `python collector.py`. The script will generate fake sensor data at 50Hz, allowing you to test the file saving and folder creation logic.

## 7. Troubleshooting

- **"Failed to initialize Serial Reader"**: The ESP32 is not connected, or the COM port is currently in use by the Arduino IDE Serial Monitor. Close the Serial Monitor. For Bluetooth, ensure the device is powered and paired.
- **"Error saving recording: Invalid recording frames. Missing required features."**: The ESP32 firmware was modified and is not outputting the exact 13 features expected by the `dataset_manager.py` schema.
- **"No frames were captured"**: You pressed start and stop too quickly, or the ESP32 is connected but not transmitting (check wiring).
