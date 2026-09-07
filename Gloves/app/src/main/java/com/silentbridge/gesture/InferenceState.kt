package com.silentbridge.gesture

enum class InferenceState {
    DISCONNECTED,
    CONNECTED,
    CALIBRATING,
    READY,
    START_BUTTON_PRESSED,
    RECORDING,
    GESTURE_DETECTED,
    PREPROCESSING,
    MODEL_INFERENCE,
    DISPLAY_RESULT,
    RESULT_FROZEN,
    ERROR
}
