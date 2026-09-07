package com.silentbridge.gesture

import android.util.Log
import com.silentbridge.domain.model.SensorFrame
import com.silentbridge.domain.model.GestureResult
import com.silentbridge.ml.GestureClassifier
import com.silentbridge.ml.GesturePreprocessor
import com.silentbridge.ml.LabelMapper
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

class GestureEngine(
    private val motionDetector: MotionDetector,
    private val recorder: GestureRecorder,
    private val preprocessor: GesturePreprocessor,
    private val classifier: GestureClassifier,
    private val labelMapper: LabelMapper
) {
    private val _state = MutableStateFlow(InferenceState.DISCONNECTED)
    val state: StateFlow<InferenceState> = _state.asStateFlow()

    private val _result = MutableStateFlow<GestureResult?>(null)
    val result: StateFlow<GestureResult?> = _result.asStateFlow()

    private val _topPredictions = MutableStateFlow<List<GestureResult>>(emptyList())
    val topPredictions: StateFlow<List<GestureResult>> = _topPredictions.asStateFlow()

    private var gyroThreshold = 0.0
    private var calibrationData = mutableListOf<Double>()
    private val CALIBRATION_FRAMES = 150 // 3 seconds at 50Hz
    private var inferenceLocked = false

    companion object {
        private const val TAG = "GestureEngine"
        private const val GYRO_MARGIN = 35.0
    }

    fun onBluetoothConnected() {
        if (_state.value == InferenceState.DISCONNECTED) {
            _state.value = InferenceState.CONNECTED
            startCalibration()
        }
    }

    fun onBluetoothDisconnected() {
        _state.value = InferenceState.DISCONNECTED
        inferenceLocked = false
    }

    private fun startCalibration() {
        _state.value = InferenceState.CALIBRATING
        calibrationData.clear()
        Log.d(TAG, "Calibration started")
    }

    fun startSession() {
        if (_state.value == InferenceState.READY || _state.value == InferenceState.RESULT_FROZEN || _state.value == InferenceState.ERROR) {
            _state.value = InferenceState.START_BUTTON_PRESSED
            _result.value = null
            _topPredictions.value = emptyList()
            recorder.clear()
            inferenceLocked = false
            Log.d(TAG, "START pressed - session initialized")
            _state.value = InferenceState.RECORDING
            recorder.start()
        }
    }

    fun resetEngine() {
        _state.value = InferenceState.READY
        _result.value = null
        _topPredictions.value = emptyList()
        recorder.clear()
        inferenceLocked = false
        Log.d(TAG, "Engine reset to READY")
    }

    fun stopSession() {
        _state.value = InferenceState.READY
        _result.value = null
        _topPredictions.value = emptyList()
        recorder.clear()
        inferenceLocked = false
        Log.d(TAG, "Session stopped")
    }

    fun onNewFrame(frame: SensorFrame) {
        val magnitude = motionDetector.calculateMagnitude(frame)

        when (_state.value) {
            InferenceState.CALIBRATING -> {
                calibrationData.add(magnitude)
                if (calibrationData.size >= CALIBRATION_FRAMES) {
                    val maxNoise = calibrationData.maxOrNull() ?: 0.0
                    gyroThreshold = maxNoise + GYRO_MARGIN
                    Log.d(TAG, "Calibration finished. Threshold: $gyroThreshold")
                    _state.value = InferenceState.READY
                }
            }
            InferenceState.RECORDING -> {
                recorder.addFrame(frame)
                val isQuiet = !motionDetector.isMoving(magnitude, gyroThreshold)
                if (recorder.updateIdleState(isQuiet)) {
                    Log.d(TAG, "Gesture ended.")
                    val gestureFrames = recorder.getValidGesture()
                    if (gestureFrames != null) {
                        Log.d(TAG, "Frames collected: ${gestureFrames.size}. Moving to GESTURE_DETECTED")
                        _state.value = InferenceState.GESTURE_DETECTED
                        processGesture(gestureFrames.toList()) // Immutable copy
                    } else {
                        Log.d(TAG, "Gesture too short. Discarding.")
                        recorder.clear()
                        recorder.start()
                    }
                }
            }
            else -> {}
        }
    }

    private fun processGesture(frames: List<SensorFrame>) {
        if (inferenceLocked) {
            Log.d(TAG, "Inference locked, skipping")
            return
        }
        
        _state.value = InferenceState.PREPROCESSING
        try {
            Log.d(TAG, "Preprocessing started. Captured frames: ${frames.size}")
            val startTime = System.currentTimeMillis()
            val inputTensor = preprocessor.preprocess(frames)
            val preprocessTime = System.currentTimeMillis() - startTime
            Log.d(TAG, "Preprocessing time: ${preprocessTime}ms")
            
            _state.value = InferenceState.MODEL_INFERENCE
            Log.d(TAG, "Model inference started")
            val inferenceStartTime = System.currentTimeMillis()
            val outputProbabilities = classifier.classify(inputTensor)
            val inferenceTime = System.currentTimeMillis() - inferenceStartTime
            Log.d(TAG, "Inference time: ${inferenceTime}ms")
            
            _state.value = InferenceState.DISPLAY_RESULT
            
            val topResults = outputProbabilities.mapIndexed { index, prob ->
                labelMapper.getLabel(index) to prob
            }.sortedByDescending { it.second }
            
            if (topResults.isNotEmpty()) {
                val winner = topResults[0]
                Log.i(TAG, "Final prediction: ${winner.first} (${String.format("%.4f", winner.second)})")
                Log.i(TAG, "Top 3 predictions:")
                topResults.take(3).forEachIndexed { i, res ->
                    Log.i(TAG, "  ${i+1}. ${res.first} = ${String.format("%.4f", res.second)}")
                }
                
                // Construct GestureResult with raw frames for feedback
                _result.value = GestureResult(
                    gestureName = winner.first,
                    confidence = winner.second,
                    topPredictions = topResults, // All classes
                    frames = frames // RAW frames
                )
                
                // For UI display of top results
                _topPredictions.value = topResults.take(3).map { GestureResult(it.first, it.second) }
                
                inferenceLocked = true
                _state.value = InferenceState.RESULT_FROZEN
                Log.d(TAG, "Inference locked. State: RESULT_FROZEN")
            } else {
                _state.value = InferenceState.ERROR
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error processing gesture: ${e.message}")
            _state.value = InferenceState.ERROR
        }
    }
}
