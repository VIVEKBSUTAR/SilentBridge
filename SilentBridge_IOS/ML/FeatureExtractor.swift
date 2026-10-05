import Foundation

/// Extracts 13 raw float features from a SensorFrame in the exact feature ordering expected by the model.
public struct FeatureExtractor: Sendable {
    public init() {}
    
    /// Extract 13 features: [thumb, index, middle, ring, little, ax, ay, az, gx, gy, gz, pitch, roll]
    public func extract(frame: SensorFrame) -> [Float] {
        [
            Float(frame.thumb),
            Float(frame.index),
            Float(frame.middle),
            Float(frame.ring),
            Float(frame.little),
            frame.ax,
            frame.ay,
            frame.az,
            frame.gx,
            frame.gy,
            frame.gz,
            frame.pitch,
            frame.roll
        ]
    }
    
    public func extractAll(frames: [SensorFrame]) -> [[Float]] {
        frames.map { extract(frame: $0) }
    }
}
