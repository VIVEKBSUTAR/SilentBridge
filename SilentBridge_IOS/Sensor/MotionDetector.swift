import Foundation

/// Motion detector using gyroscope 3-axis magnitude to detect when the hand starts/stops moving.
public struct MotionDetector: Sendable {
    public init() {}
    
    /// Calculates the 3D gyroscope vector magnitude: sqrt(gx^2 + gy^2 + gz^2).
    public func calculateMagnitude(frame: SensorFrame) -> Double {
        let gx = Double(frame.gx)
        let gy = Double(frame.gy)
        let gz = Double(frame.gz)
        return sqrt(gx * gx + gy * gy + gz * gz)
    }
    
    /// Returns true if gyroscope vector magnitude exceeds dynamic motion threshold.
    public func isMoving(magnitude: Double, threshold: Double) -> Bool {
        return magnitude > threshold
    }
}
