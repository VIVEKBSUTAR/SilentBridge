#include <Wire.h>
#include <math.h>
#include "BluetoothSerial.h"

// --- Check Bluetooth Configuration ---
#if !defined(CONFIG_BT_ENABLED) || !defined(CONFIG_BLUEDROID_ENABLED)
#error Bluetooth is not enabled! Please update your board configuration in the Arduino IDE.
#endif

BluetoothSerial SerialBT;

// --- 1. Hall Sensor Pin Definitions (The Fingers) ---
const int THUMB_PIN  = 32;
const int INDEX_PIN  = 25;
const int MIDDLE_PIN = 35;
const int RING_PIN   = 33;
const int PINKY_PIN  = 34; // ADC2 pin (Works flawlessly because Wi-Fi is OFF)

// --- 2. MPU6050 Definitions (The Wrist) ---
const int MPU_ADDR = 0x68; // Standard I2C address for MPU6050

void setup() {
  // 1. Start standard USB Serial (for debugging via cable)
  Serial.begin(115200);
  
  // 2. Start Bluetooth Serial (for wireless ML streaming)
  SerialBT.begin("SilentBridge"); // Changed from "SignLanguageGlove" to "SilentBridge"
  Serial.println("Bluetooth Started! Ready to pair to laptop...");
  
  // 3. Start the I2C bus for the MPU6050 (Defaults: SDA = G21, SCL = G22)
  Wire.begin(); 
  
  // 4. Wake up the MPU6050
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x6B); // Point to the Power Management Register
  Wire.write(0x00); // Write 0 to disable sleep mode
  Wire.endTransmission(true);
  
  // Give the hardware a moment to stabilize
  delay(100);
}

void loop() {
  // --- STEP 1: READ FINGER BENDING (HALL SENSORS) ---
  int thumbVal  = analogRead(THUMB_PIN);
  int indexVal  = analogRead(INDEX_PIN);
  int middleVal = analogRead(MIDDLE_PIN);
  int ringVal   = analogRead(RING_PIN);
  int pinkyVal  = analogRead(PINKY_PIN);

  // --- STEP 2: READ HAND ORIENTATION & MOTION (MPU6050) ---
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x3B); // Start reading at the first Accelerometer register
  Wire.endTransmission(false);
  Wire.requestFrom(MPU_ADDR, 14, true); // Request 14 registers (6 accel, 2 temp, 6 gyro)
  
  int16_t accX  = Wire.read() << 8 | Wire.read();
  int16_t accY  = Wire.read() << 8 | Wire.read();
  int16_t accZ  = Wire.read() << 8 | Wire.read();
  int16_t temp  = Wire.read() << 8 | Wire.read();
  int16_t gyroX = Wire.read() << 8 | Wire.read();
  int16_t gyroY = Wire.read() << 8 | Wire.read();
  int16_t gyroZ = Wire.read() << 8 | Wire.read();

  // Convert raw accelerometer readings into Pitch and Roll (in degrees)
  // pitch = angle of tilt forward/backward
  // roll  = angle of tilt side-to-side
  float pitch = atan2(-accX, sqrt((float)accY * accY + (float)accZ * accZ)) * 180.0 / M_PI;
  float roll  = atan2((float)accY, (float)accZ) * 180.0 / M_PI;

  // --- STEP 3: STREAM DATA VIA BLUETOOTH ---
  // CSV Format: [Thumb, Index, Middle, Ring, Pinky, Roll, Pitch, AccX, AccY, AccZ, GyroX, GyroY, GyroZ]
  SerialBT.print(thumbVal);  SerialBT.print(",");
  SerialBT.print(indexVal);  SerialBT.print(",");
  SerialBT.print(middleVal); SerialBT.print(",");
  SerialBT.print(ringVal);   SerialBT.print(",");
  SerialBT.print(pinkyVal);  SerialBT.print(",");
  
  SerialBT.print(roll, 2);   SerialBT.print(",");
  SerialBT.print(pitch, 2);  SerialBT.print(","); 
  
  SerialBT.print(accX);      SerialBT.print(",");
  SerialBT.print(accY);      SerialBT.print(",");
  SerialBT.print(accZ);      SerialBT.print(","); 
  
  SerialBT.print(gyroX);     SerialBT.print(",");
  SerialBT.print(gyroY);     SerialBT.print(",");
  SerialBT.println(gyroZ);   // The final value gets the println to end the frame!

  // --- STEP 4: STREAM DATA VIA USB BACKUP ---
  // (Identical output for the Arduino Serial Plotter)
  Serial.print(thumbVal);  Serial.print(",");
  Serial.print(indexVal);  Serial.print(",");
  Serial.print(middleVal); Serial.print(",");
  Serial.print(ringVal);   Serial.print(",");
  Serial.print(pinkyVal);  Serial.print(",");
  
  Serial.print(roll, 2);   Serial.print(",");
  Serial.print(pitch, 2);  Serial.print(","); 
  
  Serial.print(accX);      Serial.print(",");
  Serial.print(accY);      Serial.print(",");
  Serial.print(accZ);      Serial.print(","); 
  
  Serial.print(gyroX);     Serial.print(",");
  Serial.print(gyroY);     Serial.print(",");
  Serial.println(gyroZ); 

  // --- STEP 5: TIMING ---
  // Delay 50ms to lock the sample rate at exactly 20Hz (20 frames per second).
  delay(50);
}
