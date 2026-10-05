import Foundation

/// Entry model representing feedback given by user for gesture classifier predictions.
public struct FeedbackEntry: Identifiable, Codable, Sendable, Equatable {
    public var id: UUID
    public var predictedLabel: String
    public var correctLabel: String
    public var confidence: Float
    public var isConfirmed: Bool
    public var timestamp: Date
    public var sampleCount: Int
    
    public init(
        id: UUID = UUID(),
        predictedLabel: String,
        correctLabel: String,
        confidence: Float,
        isConfirmed: Bool,
        timestamp: Date = Date(),
        sampleCount: Int = 0
    ) {
        self.id = id
        self.predictedLabel = predictedLabel
        self.correctLabel = correctLabel
        self.confidence = confidence
        self.isConfirmed = isConfirmed
        self.timestamp = timestamp
        self.sampleCount = sampleCount
    }
}
