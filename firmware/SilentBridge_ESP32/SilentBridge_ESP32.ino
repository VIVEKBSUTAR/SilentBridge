/*
 * SilentBridge Firmware
 * 
 * Feature Order:
 * thumb
 * index
 * middle
 * ring
 * little
 * ax
 * ay
 * az
 * gx
 * gy
 * gz
 * pitch
 * roll
 * 
 * Sampling Rate: 50Hz
 * Bluetooth Device Name: SilentBridge
 */

#include <Wire.h>
#include "BluetoothSerial.h"

#if !defined(CONFIG_BT_ENABLED) || !defined(CONFIG_BLUEDROID_ENABLED)
#error Bluetooth is not enabled! Please run `make menuconfig` to and enable it
#endif

BluetoothSerial SerialBT;

// Hall Sensor Pins
const int PIN_THUMB  = 32;
const int PIN_INDEX  = 25;
const int PIN_MIDDLE = 35;
const int PIN_RING   = 33;
const int PIN_LITTLE = 34;

// MPU6050 I2C Pins
const int I2C_SDA = 21;
const int I2C_SCL = 22;

const int MPU_ADDR = 0x68;
bool mpuConnected = false;

const unsigned long SAMPLE_INTERVAL_MS = 20; // 50 Hz
unsigned long lastSampleTime = 0;

void setup() {
  Serial.begin(115200);
  SerialBT.begin("SilentBridge"); // Bluetooth device name
  
  // Wait for serial to initialize, but don't block forever
  unsigned long startWait = millis();
  while (!Serial && (millis() - startWait < 2000));
  
  Wire.begin(I2C_SDA, I2C_SCL);
  
  // Initialize MPU6050 directly via registers
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x6B);  // PWR_MGMT_1 register
  Wire.write(0);     // Set to zero (wakes up the MPU-6050)
  byte error = Wire.endTransmission();
  
  if (error == 0) {
    mpuConnected = true;
  } else {
    mpuConnected = false;
  }
  
  // Initialize Analog pins
  pinMode(PIN_THUMB, INPUT);
  pinMode(PIN_INDEX, INPUT);
  pinMode(PIN_MIDDLE, INPUT);
  pinMode(PIN_RING, INPUT);
  pinMode(PIN_LITTLE, INPUT);
}

void loop() {
  unsigned long currentTime = millis();
  
  if (currentTime - lastSampleTime >= SAMPLE_INTERVAL_MS) {
    lastSampleTime = currentTime;
    
    // Read Hall Sensors
    int thumb  = analogRead(PIN_THUMB);
    int index  = analogRead(PIN_INDEX);
    int middle = analogRead(PIN_MIDDLE);
    int ring   = analogRead(PIN_RING);
    int little = analogRead(PIN_LITTLE);
    
    float ax = 0.0, ay = 0.0, az = 0.0;
    float gx = 0.0, gy = 0.0, gz = 0.0;
    float pitch = 0.0, roll = 0.0;
    
    if (mpuConnected) {
      Wire.beginTransmission(MPU_ADDR);
      Wire.write(0x3B);  // starting with register 0x3B (ACCEL_XOUT_H)
      byte transError = Wire.endTransmission(false);
      
      if (transError == 0) {
        // Request 14 registers (6 accel, 2 temp, 6 gyro)
        Wire.requestFrom(MPU_ADDR, 14, true);
        
        if (Wire.available() >= 14) {
          int16_t accelX = Wire.read() << 8 | Wire.read();
          int16_t accelY = Wire.read() << 8 | Wire.read();
          int16_t accelZ = Wire.read() << 8 | Wire.read();
          int16_t tempRaw = Wire.read() << 8 | Wire.read(); // Read temperature and discard
          int16_t gyroX = Wire.read() << 8 | Wire.read();
          int16_t gyroY = Wire.read() << 8 | Wire.read();
          int16_t gyroZ = Wire.read() << 8 | Wire.read();
          
          // Convert to g (default +/-2g range uses 16384 LSB/g)
          ax = accelX / 16384.0;
          ay = accelY / 16384.0;
          az = accelZ / 16384.0;
          
          // Convert to deg/s (default +/-250deg/s range uses 131 LSB/deg/s)
          gx = gyroX / 131.0;
          gy = gyroY / 131.0;
          gz = gyroZ / 131.0;
          
          pitch = atan2(-ax, sqrt(ay * ay + az * az)) * 180.0 / PI;
          roll  = atan2(ay, az) * 180.0 / PI;
        } else {
          // I2C read failed, reset connection flag to try re-init later if needed,
          // or just leave as 0 for this frame.
        }
      }
    }
    
    // Construct JSON Packet using a char buffer for clean transmission
    char packet[256];
    snprintf(packet, sizeof(packet),
             "{\"timestamp\":%lu,\"thumb\":%d,\"index\":%d,\"middle\":%d,\"ring\":%d,\"little\":%d,"
             "\"ax\":%.3f,\"ay\":%.3f,\"az\":%.3f,\"gx\":%.3f,\"gy\":%.3f,\"gz\":%.3f,\"pitch\":%.2f,\"roll\":%.2f}",
             currentTime, thumb, index, middle, ring, little, 
             ax, ay, az, gx, gy, gz, pitch, roll);
             
    // Always transmit over USB Serial
    Serial.println(packet);
    
    // Only transmit over Bluetooth if a client is actively connected
    if (SerialBT.hasClient()) {
      SerialBT.println(packet);
    }
  }
}
