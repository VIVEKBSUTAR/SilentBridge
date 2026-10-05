import Foundation
import Combine

/// Core State Machine Orchestrator for Gesture Telemetry, Calibration, Recorder, and Classifier.
public final class GestureEngine: ObservableObject, @unchecked Sendable {
    
    // MARK: - Published State
    @Published public private(set) var state: InferenceState = .disconnected
    @Published public private(set) var result: GestureResult? = nil
    @Published public private(set) var topPredictions: [GestureResult] = []
    
    // Auto-loop mode flag
    private var autoLoopActive: Bool = false
    public var onAutoGestureResult: ((GestureResult) -> Bool)? = nil
    
    // Calibration State
    private let calibrationFramesRequired: Int = 150
    private var calibrationFrames: [SensorFrame] = []
    private var calibrationSumGx: Double = 0
    private var calibrationSumGy: Double = 0
    private var calibrationSumGz: Double = 0
    
    private var biasGx: Double = 0
    private var biasGy: Double = 0
    private var biasGz: Double = 0
    private var gyroThreshold: Double = 30.0
    private var inferenceLocked: Bool = false
    
    private static let gyroMargin: Double = 15.0
    
    // Dependencies
    private let motionDetector = MotionDetector()
    private let recorder = GestureRecorder()
    private let preprocessor = GesturePreprocessor()
    private let classifier = GestureClassifier()
    private let labelMapper = LabelMapper()
    
    public init() {}
    
    // MARK: - Lifecycle Events
    
    public func onBluetoothConnected() {
        if state == .disconnected {
            state = .connected
            startCalibration()
        }
    }
    
    public func onBluetoothDisconnected() {
        state = .disconnected
        autoLoopActive = false
        inferenceLocked = false
    }
    
    public func startCalibration() {
        state = .calibrating
        calibrationFrames.removeAll()
        calibrationSumGx = 0
        calibrationSumGy = 0
        calibrationSumGz = 0
    }
    
    public func startSession() {
        if state == .ready || state == .resultFrozen || state == .error {
            autoLoopActive = false
            beginRecording()
        }
    }
    
    public func startAutoLoop() {
        if state == .ready || state == .resultFrozen || state == .error {
            autoLoopActive = true
            beginRecording()
        }
    }
    
    public func stopAutoLoop() {
        autoLoopActive = false
        state = .ready
        result = nil
        topPredictions.removeAll()
        recorder.clear()
        inferenceLocked = false
    }
    
    public func resetEngine() {
        state = .ready
        result = nil
        topPredictions.removeAll()
        recorder.clear()
        inferenceLocked = false
    }
    
    public func stopSession() {
        autoLoopActive = false
        state = .ready
        result = nil
        topPredictions.removeAll()
        recorder.clear()
        inferenceLocked = false
    }
    
    private func beginRecording() {
        state = .startButtonPressed
        result = nil
        topPredictions.removeAll()
        recorder.clear()
        inferenceLocked = false
        state = .recording
        recorder.start()
    }
    
    // MARK: - Frame Processing
    
    public func onNewFrame(_ frame: SensorFrame) {
        switch state {
        case .calibrating:
            calibrationSumGx += Double(frame.gx)
            calibrationSumGy += Double(frame.gy)
            calibrationSumGz += Double(frame.gz)
            calibrationFrames.append(frame)
            
            if calibrationFrames.count >= calibrationFramesRequired {
                biasGx = calibrationSumGx / Double(calibrationFramesRequired)
                biasGy = calibrationSumGy / Double(calibrationFramesRequired)
                biasGz = calibrationSumGz / Double(calibrationFramesRequired)
                
                var maxNoise: Double = 0
                for f in calibrationFrames {
                    let cx = Double(f.gx) - biasGx
                    let cy = Double(f.gy) - biasGy
                    let cz = Double(f.gz) - biasGz
                    let mag = sqrt(cx * cx + cy * cy + cz * cz)
                    if mag > maxNoise { maxNoise = mag }
                }
                
                gyroThreshold = maxNoise + Self.gyroMargin
                calibrationFrames.removeAll()
                state = .ready
            }
            
        case .recording:
            let calibratedFrame = SensorFrame(
                timestamp: frame.timestamp,
                thumb: frame.thumb,
                index: frame.index,
                middle: frame.middle,
                ring: frame.ring,
                little: frame.little,
                ax: frame.ax,
                ay: frame.ay,
                az: frame.az,
                gx: Float(Double(frame.gx) - biasGx),
                gy: Float(Double(frame.gy) - biasGy),
                gz: Float(Double(frame.gz) - biasGz),
                pitch: frame.pitch,
                roll: frame.roll
            )
            
            recorder.addFrame(calibratedFrame)
            
            let magnitude = motionDetector.calculateMagnitude(frame: calibratedFrame)
            let isQuiet = !motionDetector.isMoving(magnitude: magnitude, threshold: gyroThreshold)
            
            if recorder.updateIdleState(isQuiet: isQuiet) {
                if let gestureFrames = recorder.getValidGesture() {
                    state = .gestureDetected
                    processGesture(frames: gestureFrames)
                } else {
                    recorder.clear()
                    recorder.start()
                }
            }
            
        default:
            break
        }
    }
    
    private func processGesture(frames: [SensorFrame]) {
        guard !inferenceLocked else { return }
        
        state = .preprocessing
        let inputMatrix = preprocessor.preprocess(frames: frames)
        
        state = .modelInference
        let outputProbabilities = classifier.classify(matrix: inputMatrix)
        
        state = .displayResult
        
        let indexedResults = outputProbabilities.enumerated().map { (index, prob) in
            (name: labelMapper.getLabel(for: index), score: prob)
        }.sorted(by: { $0.score > $1.score })
        
        if let winner = indexedResults.first {
            let gestureRes = GestureResult(
                gestureName: winner.name,
                confidence: winner.score,
                topPredictions: indexedResults,
                frames: frames
            )
            
            if autoLoopActive {
                let accepted = onAutoGestureResult?(gestureRes) ?? false
                if accepted {
                    // Reset and auto-restart recording loop
                    beginRecording()
                } else {
                    beginRecording()
                }
            } else {
                self.result = gestureRes
                self.topPredictions = indexedResults.prefix(3).map { GestureResult(gestureName: $0.name, confidence: $0.score) }
                self.inferenceLocked = true
                self.state = .resultFrozen
            }
        } else {
            if autoLoopActive {
                beginRecording()
            } else {
                state = .error
            }
        }
    }
}
