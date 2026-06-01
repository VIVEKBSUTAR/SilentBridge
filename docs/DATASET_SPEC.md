# SilentBridge Dataset Specification

This document is the canonical specification for the SilentBridge dataset format. All future preprocessing, data augmentation, and machine learning models must strictly adhere to the schema and conventions defined here.

## 1. Global Specifications

- **Sampling Rate**: 50 Hz (1 frame per 20 milliseconds)
- **Features Per Frame**: Exactly 13 (5 Finger + 8 Motion)
- **File Format**: JSON (`.json`)
- **Character Encoding**: UTF-8

## 2. Feature Definitions & Sensor Units

Every recorded frame must contain exactly the following 13 features, plus a timestamp.

### Hall Effect Sensors (Finger Flexion)
*Measures magnetic field strength relative to finger bend.*
- `thumb`: Integer (0-4095 typical raw ADC, or calibrated 0-100)
- `index`: Integer
- `middle`: Integer
- `ring`: Integer
- `little`: Integer

### MPU6050 Motion Tracking
*Measures hand acceleration, rotation, and orientation.*
- **Accelerometer** (Units: *g*, gravitational force)
  - `ax`: Float
  - `ay`: Float
  - `az`: Float
- **Gyroscope** (Units: degrees per second, *°/s*)
  - `gx`: Float
  - `gy`: Float
  - `gz`: Float
- **Orientation** (Derived, Units: degrees, *°*)
  - `pitch`: Float
  - `roll`: Float

## 3. Recording Format (JSON Schema)

Every saved recording file must follow this exact JSON structure:

```json
{
  "label": "HELLO",
  "sample_id": "HELLO_0001",
  "recorded_at": "2026-06-01T10:20:30.123456",
  "frame_count": 128,
  "frames": [
    {
      "timestamp": 1712345678,
      "thumb": 2140,
      "index": 3050,
      "middle": 2870,
      "ring": 1920,
      "little": 1750,
      "ax": 0.15,
      "ay": 1.23,
      "az": 9.42,
      "gx": 22.1,
      "gy": -4.8,
      "gz": 35.6,
      "pitch": 12.4,
      "roll": -4.1
    }
  ]
}
```

## 4. Folder Structure

Datasets are organized hierarchically by gesture label under `data/raw/`.

```
data/
└── raw/
    ├── HELLO/
    ├── HELP/
    ├── WATER/
    ├── FOOD/
    ├── YES/
    ├── NO/
    ├── THANK_YOU/
    └── MEDICINE/
```

## 5. Naming Convention

Files must be named sequentially using the format `<LABEL>_<4-DIGIT-ID>.json`.

**Examples:**
- `HELLO_0001.json`
- `HELLO_0002.json`
- `HELP_0001.json`

**Rules:**
- Padding: IDs must be strictly padded to 4 digits with leading zeros.
- Uniqueness: Sample IDs must never be duplicated within a label directory.
- Case: The label prefix must exactly match the parent folder name (all caps).

## 6. Validation Rules

A recording is only valid and ready for ML processing if:
1. It is valid, parsable JSON.
2. The `label` field matches an officially supported vocabulary term.
3. The `frame_count` matches the exact length of the `frames` array.
4. The `frames` array is not empty.
5. **Every single frame** contains exactly the 14 keys defined above (`timestamp` + 13 features). Missing keys will invalidate the entire recording.
