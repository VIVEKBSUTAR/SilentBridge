#include <Wire.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>

Adafruit_MPU6050 mpu;

// Hall Sensor Pins
const int PIN_THUMB  = 32;
const int PIN_INDEX  = 33;
const int PIN_MIDDLE = 34;
const int PIN_RING   = 35;
const int PIN_LITTLE = 36;

// MPU6050 I2C Pins
const int I2C_SDA = 21;
const int I2C_SCL = 22;

const unsigned long SAMPLE_INTERVAL_MS = 20; // 50 Hz
unsigned long lastSampleTime = 0;

void setup() {
  Serial.begin(115200);
  
  // Wait for serial to initialize, but don't block forever
  unsigned long startWait = millis();
  while (!Serial && (millis() - startWait < 2000));
  
  // Initialize I2C with specific pins
  Wire.begin(I2C_SDA, I2C_SCL);
  
  // Initialize MPU6050
  // Note: We avoid printing any initialization status to keep output STRICTLY JSON
  mpu.begin();
  
  mpu.setAccelerometerRange(MPU6050_RANGE_8_G);
  mpu.setGyroRange(MPU6050_RANGE_500_DEG);
  mpu.setFilterBandwidth(MPU6050_BAND_21_HZ);
  
  // Initialize Analog pins (not strictly necessary for ESP32 analogRead, but good practice)
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
    
    // Read MPU6050
    sensors_event_t a, g, temp;
    mpu.getEvent(&a, &g, &temp);
    
    // Calculate Pitch and Roll from Accelerometer
    // pitch = atan2(-ax, sqrt(ay*ay + az*az)) * 180 / PI
    // roll = atan2(ay, az) * 180 / PI
    float ax = a.acceleration.x;
    float ay = a.acceleration.y;
    float az = a.acceleration.z;
    
    float pitch = atan2(-ax, sqrt(ay * ay + az * az)) * 180.0 / PI;
    float roll  = atan2(ay, az) * 180.0 / PI;
    
    // Construct JSON Packet manually to avoid heavy JSON libraries overhead on every loop
    // Ensure exactly ONE line of output
    Serial.print("{");
    Serial.print("\"timestamp\":"); Serial.print(currentTime); Serial.print(",");
    
    Serial.print("\"thumb\":"); Serial.print(thumb); Serial.print(",");
    Serial.print("\"index\":"); Serial.print(index); Serial.print(",");
    Serial.print("\"middle\":"); Serial.print(middle); Serial.print(",");
    Serial.print("\"ring\":"); Serial.print(ring); Serial.print(",");
    Serial.print("\"little\":"); Serial.print(little); Serial.print(",");
    
    Serial.print("\"ax\":"); Serial.print(ax, 3); Serial.print(",");
    Serial.print("\"ay\":"); Serial.print(ay, 3); Serial.print(",");
    Serial.print("\"az\":"); Serial.print(az, 3); Serial.print(",");
    
    Serial.print("\"gx\":"); Serial.print(g.gyro.x, 3); Serial.print(",");
    Serial.print("\"gy\":"); Serial.print(g.gyro.y, 3); Serial.print(",");
    Serial.print("\"gz\":"); Serial.print(g.gyro.z, 3); Serial.print(",");
    
    Serial.print("\"pitch\":"); Serial.print(pitch, 2); Serial.print(",");
    Serial.print("\"roll\":"); Serial.print(roll, 2);
    
    Serial.println("}");
  }
}
