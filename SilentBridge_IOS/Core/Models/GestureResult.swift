import Foundation

/// Prediction output from the gesture classifier engine.
public struct GestureResult: Identifiable, Sendable, Equatable {
    public var id: UUID = UUID()
    public var gestureName: String
    public var confidence: Float
    public var adjustedConfidence: Float
    public var topPredictions: [(name: String, score: Float)]
    public var frames: [SensorFrame]
    public var timestamp: Date
    
    public init(
        gestureName: String,
        confidence: Float,
        adjustedConfidence: Float? = nil,
        topPredictions: [(name: String, score: Float)] = [],
        frames: [SensorFrame] = [],
        timestamp: Date = Date()
    ) {
        self.gestureName = gestureName
        self.confidence = confidence
        self.adjustedConfidence = adjustedConfidence ?? confidence
        self.topPredictions = topPredictions
        self.frames = frames
        self.timestamp = timestamp
    }
    
    public static func == (lhs: GestureResult, rhs: GestureResult) -> Bool {
        lhs.id == rhs.id && lhs.gestureName == rhs.gestureName && lhs.confidence == rhs.confidence
    }
}
