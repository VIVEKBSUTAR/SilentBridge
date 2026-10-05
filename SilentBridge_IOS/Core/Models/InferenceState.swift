import Foundation

/// Real-time state machine for gesture capture, motion detection, and ML inference.
public enum InferenceState: String, Codable, Sendable, CustomStringConvertible {
    case disconnected = "DISCONNECTED"
    case connected = "CONNECTED"
    case calibrating = "CALIBRATING"
    case ready = "READY"
    case startButtonPressed = "START_BUTTON_PRESSED"
    case recording = "RECORDING"
    case gestureDetected = "GESTURE_DETECTED"
    case preprocessing = "PREPROCESSING"
    case modelInference = "MODEL_INFERENCE"
    case displayResult = "DISPLAY_RESULT"
    case resultFrozen = "RESULT_FROZEN"
    case error = "ERROR"
    
    public var description: String { rawValue }
    
    public var userFriendlyText: String {
        switch self {
        case .disconnected: return "Glove Disconnected"
        case .connected: return "Initializing Glove..."
        case .calibrating: return "Calibrating Gyroscope (Hold Still)..."
        case .ready: return "Ready for Gestures"
        case .startButtonPressed: return "Preparing Recorder..."
        case .recording: return "Listening for Gesture..."
        case .gestureDetected: return "Gesture Captured"
        case .preprocessing: return "Normalizing Features..."
        case .modelInference: return "Classifying Gesture..."
        case .displayResult: return "Gesture Classified"
        case .resultFrozen: return "Awaiting Verification"
        case .error: return "Inference Error"
        }
    }
}
