# SilentBridge iOS — TFLite Integration Guide

## Why This Step Is Required

The gesture classifier (`GestureClassifier.swift`) runs a **BiLSTM neural network** trained with TensorFlow Select ops (FlexDelegate on Android). This model **cannot run on standard TFLite kernels** — it requires the `TensorFlowLiteSelectTfOps` extension.

Until the TFLite Swift package is linked, the app builds and runs using a **heuristic fallback** that approximates gesture detection from raw finger sensor averages. This is for development/UI testing only.

## Integration Steps (Xcode UI)

### 1. Open the Project
```
open /Volumes/APFS/AppleDev/Projects/SilentBridge_IOS/SilentBridge_IOS.xcodeproj
```

### 2. Add Swift Package Dependencies

In Xcode menu: **File → Add Package Dependencies...**

Add these two packages:

| Package | URL | Version |
|---------|-----|---------|
| TensorFlowLiteSwift | `https://github.com/google/tensorflow` | **Up to next major from 2.15.0** |
| TensorFlowLiteSelectTfOps | Same repo (select from same resolution) | Same version |

> **Alternative (more stable):** Use the pre-built XCFramework from the TFLite CocoaPods:
> ```
> # Only if you're using CocoaPods
> pod 'TensorFlowLiteSwift', '~> 2.15'
> pod 'TensorFlowLiteSelectTfOps', '~> 2.15'
> ```

### 3. Link Frameworks to Target

After adding the package, ensure both products are linked to **SilentBridge_IOS** target:
- `TensorFlowLite` → Link Binary With Libraries
- `TensorFlowLiteSelectTfOps` → Link Binary With Libraries

### 4. Activate Real Inference

Once TFLite is linked, the `GestureClassifier.swift` automatically uses real inference because of this guard:

```swift
#if canImport(TensorFlowLite)
import TensorFlowLite
// ... real TFLite code runs here
#endif
```

No code changes are needed — the `canImport` conditional compiles to the real path automatically.

### 5. Remove Heuristic Fallback (Optional Cleanup)

After confirming real inference works, remove the `heuristicFallback()` method from `GestureClassifier.swift`.

## Model Specifications

| Property | Value |
|----------|-------|
| File | `silentbridge_standard.tflite` |
| Architecture | BiLSTM (bidirectional LSTM) |
| Input tensor | `[1, 100, 13]` float32 |
| Output tensor | `[1, N]` float32 softmax |
| Select ops required | Yes (FlexDelegate) |
| Android delegate | `FlexDelegate` |
| iOS delegate | `TensorFlowLiteSelectTfOps` |

## Preprocessing Pipeline

The iOS preprocessing pipeline in `GesturePreprocessor.swift` exactly mirrors the Android implementation:

1. **Feature extraction** — 13 features per frame: `[thumb, index, middle, ring, little, ax, ay, az, gx, gy, gz, pitch, roll]`
2. **Finger normalization** — ADC values divided by 4095.0 → [0.0, 1.0]
3. **Resampling** — Linear interpolation to exactly 100 frames
4. **Standard scaling** — Z-score normalization for IMU columns 5..12 using `scaler_params.json`

## Verification

After linking TFLite, build and check the console output:
```
[GestureClassifier] ✅ Model loaded. Classes: 13, Input: [1, 100, 13]
```

If you see:
```
[GestureClassifier] ⚠️  TensorFlowLite not linked. Running in heuristic fallback mode.
```
The package is not yet linked.
