import Foundation

/// Buffers incoming calibrated SensorFrames during active recording and detects valid gesture boundaries.
public final class GestureRecorder: @unchecked Sendable {
    public static let idleSettleFrames: Int = 15
    public static let minGestureFrames: Int = 15
    
    private var recordedFrames: [SensorFrame] = []
    private var idleCounter: Int = 0
    
    public init() {}
    
    public func start() {
        recordedFrames.removeAll()
        idleCounter = 0
    }
    
    public func addFrame(_ frame: SensorFrame) {
        recordedFrames.append(frame)
    }
    
    /// Updates idle counter based on quiet/moving state and returns true if gesture has ended.
    public func updateIdleState(isQuiet: Bool) -> Bool {
        if isQuiet {
            idleCounter += 1
        } else {
            idleCounter = 0
        }
        return idleCounter >= Self.idleSettleFrames
    }
    
    /// Extracts valid gesture frames by dropping trailing idle settle frames.
    /// Returns valid frame array if remaining frame count >= minGestureFrames, else nil.
    public func getValidGesture() -> [SensorFrame]? {
        let gestureFrames: [SensorFrame]
        if recordedFrames.count > Self.idleSettleFrames {
            gestureFrames = Array(recordedFrames.dropLast(Self.idleSettleFrames))
        } else {
            gestureFrames = []
        }
        
        if gestureFrames.count >= Self.minGestureFrames {
            return gestureFrames
        } else {
            return nil
        }
    }
    
    public func clear() {
        recordedFrames.removeAll()
        idleCounter = 0
    }
}
