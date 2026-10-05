import Foundation

// MARK: - TFLite Integration Note
//
// This classifier uses TensorFlowLiteSwift + TensorFlowLiteSelectTfOps (Flex ops).
//
// The model (silentbridge_standard.tflite) is a BiLSTM network trained with
// TensorFlow Select ops (required for LSTM/GRU on mobile), identical to the
// Android implementation.
//
// To complete TFLite integration in Xcode:
//   1. File > Add Package Dependencies...
//   2. URL: https://github.com/tensorflow/tensorflow
//   3. Branch: main  (or a release tag such as v2.15.0)
//   4. Add products: TensorFlowLiteSwift + TensorFlowLiteSelectTfOps
//   5. Ensure both are linked to the SilentBridge_IOS target
//
// Alternatively, use the CocoaPods-distributed XCFramework:
//   pod 'TensorFlowLiteSwift', '~> 2.15'
//   pod 'TensorFlowLiteSelectTfOps', '~> 2.15'
//
// Once the package is added, uncomment the TFLite code blocks below
// (search for "TFLITE_AVAILABLE") and remove the heuristic fallback.
//
// Input tensor:  [1, 100, 13]  (float32)
// Output tensor: [1, N]        (float32 softmax probabilities)

// ─────────────────────────────────────────────────────────────────────────────
// Conditional import — compiles cleanly with or without TFLite linked
// ─────────────────────────────────────────────────────────────────────────────
#if canImport(TensorFlowLite)
import TensorFlowLite
#endif

/// Machine-learning inference engine for the SilentBridge BiLSTM gesture classifier.
///
/// Architecture:
///   - Input:  [1, 100, 13] float32 — 100 timesteps × 13 features
///   - Output: [1, numClasses] float32 — softmax class probabilities
///
/// The model uses TensorFlow Select ops (FlexDelegate equivalent on iOS)
/// because BiLSTM cells require ops not present in the standard TFLite kernel set.
public final class GestureClassifier: @unchecked Sendable {

    // MARK: - Dependencies

    private let labelMapper = LabelMapper()

    // MARK: - Model Constants

    private static let modelName  = "silentbridge_standard"
    private static let inputFrames  = 100
    private static let inputFeatures = 13

    // MARK: - TFLite Interpreter (lazy-loaded, thread-safe via serial queue)

    #if canImport(TensorFlowLite)
    private var interpreter: Interpreter?
    private var numClasses: Int = 0
    #endif

    private let inferenceQueue = DispatchQueue(label: "com.silentbridge.inference", qos: .userInteractive)
    private var modelLoaded = false

    // MARK: - Init

    public init() {
        loadModel()
    }

    // MARK: - Model Loading

    private func loadModel() {
        guard let modelURL = Bundle.main.url(forResource: Self.modelName, withExtension: "tflite") else {
            print("[GestureClassifier] ⚠️  Model file \(Self.modelName).tflite not found in bundle.")
            return
        }

        #if canImport(TensorFlowLite)
        inferenceQueue.sync { [weak self] in
            guard let self else { return }
            do {
                // Build interpreter options – Select TF Ops (FlexDelegate equivalent)
                var options = Interpreter.Options()
                options.threadCount = 2

                // Metal GPU delegate for accelerated inference on device
                let metalDelegate = MetalDelegate()
                options.delegates = [metalDelegate]

                let interp = try Interpreter(modelPath: modelURL.path, options: options)
                try interp.allocateTensors()

                // Verify input tensor shape [1, 100, 13]
                let inputTensor = try interp.input(at: 0)
                guard inputTensor.shape.dimensions == [1, Self.inputFrames, Self.inputFeatures] else {
                    print("[GestureClassifier] ⚠️  Unexpected input tensor shape: \(inputTensor.shape.dimensions). Expected [1, 100, 13].")
                    return
                }

                // Read output class count
                let outputTensor = try interp.output(at: 0)
                self.numClasses = outputTensor.shape.dimensions.last ?? 0
                self.interpreter = interp
                self.modelLoaded = true

                print("[GestureClassifier] ✅ Model loaded. Classes: \(self.numClasses), Input: \(inputTensor.shape.dimensions)")
            } catch {
                print("[GestureClassifier] ❌ Failed to load model: \(error)")
            }
        }
        #else
        // TFLite not linked yet — heuristic mode active
        print("[GestureClassifier] ⚠️  TensorFlowLite not linked. Running in heuristic fallback mode.")
        print("[GestureClassifier] ℹ️  Add TensorFlowLiteSwift + TensorFlowLiteSelectTfOps via SPM to enable real inference.")
        modelLoaded = false
        #endif
    }

    // MARK: - Inference

    /// Classifies a preprocessed [100 × 13] sequence into softmax class probabilities.
    ///
    /// - Parameter matrix: Output of `GesturePreprocessor.preprocess()` — exactly 100 rows, 13 columns.
    /// - Returns: Float array of length `numClasses` (softmax probabilities summing to ~1.0).
    public func classify(matrix: [[Float]]) -> [Float] {
        guard matrix.count == Self.inputFrames,
              matrix.first?.count == Self.inputFeatures else {
            print("[GestureClassifier] ⚠️  Invalid input shape: \(matrix.count) × \(matrix.first?.count ?? 0). Expected 100 × 13.")
            return Array(repeating: 0.0, count: labelMapper.allLabels.count)
        }

        #if canImport(TensorFlowLite)
        if modelLoaded, let interp = inferenceQueue.sync(execute: { interpreter }) {
            return runTFLiteInference(matrix: matrix, interpreter: interp)
        }
        #endif

        // Heuristic fallback — used only until TFLite package is linked.
        // Remove once real inference is active.
        return heuristicFallback(matrix: matrix)
    }

    // MARK: - TFLite Inference Implementation

    #if canImport(TensorFlowLite)
    private func runTFLiteInference(matrix: [[Float]], interpreter: Interpreter) -> [Float] {
        // Flatten [100, 13] → [1, 100, 13] contiguous float32 buffer
        var flatInput = [Float]()
        flatInput.reserveCapacity(1 * Self.inputFrames * Self.inputFeatures)
        for row in matrix {
            flatInput.append(contentsOf: row)
        }

        let inputData = Data(bytes: flatInput, count: flatInput.count * MemoryLayout<Float>.size)

        do {
            try interpreter.copy(inputData, toInputAt: 0)
            try interpreter.invoke()
            let outputTensor = try interpreter.output(at: 0)
            let outputData = outputTensor.data

            // Parse raw float bytes into probability array
            let count = outputData.count / MemoryLayout<Float>.size
            var probs = [Float](repeating: 0, count: count)
            _ = probs.withUnsafeMutableBytes { ptr in
                outputData.copyBytes(to: ptr, count: outputData.count)
            }
            return probs
        } catch {
            print("[GestureClassifier] ❌ Inference error: \(error)")
            return Array(repeating: 0.0, count: numClasses)
        }
    }
    #endif

    // MARK: - Heuristic Fallback
    //
    // This approximates BiLSTM decision boundaries using finger ADC sensor averages.
    // It is NOT a substitute for the real model. It exists solely to allow
    // development and UI testing without the TFLite package linked.
    //
    // REMOVE this method once TensorFlowLiteSwift is linked.

    private func heuristicFallback(matrix: [[Float]]) -> [Float] {
        let n = labelMapper.allLabels.count
        var scores = Array(repeating: Float(0.01), count: n)

        // Feature averages across 100 frames — columns 0..4 are normalized finger ADC [0,1]
        var avgThumb:  Float = 0
        var avgIndex:  Float = 0
        var avgMiddle: Float = 0
        var avgRing:   Float = 0
        var avgLittle: Float = 0
        var totalMotion: Float = 0

        for row in matrix {
            avgThumb  += row[0]
            avgIndex  += row[1]
            avgMiddle += row[2]
            avgRing   += row[3]
            avgLittle += row[4]
            totalMotion += abs(row[5]) + abs(row[6]) + abs(row[7])
        }

        let frames = Float(matrix.count)
        avgThumb  /= frames
        avgIndex  /= frames
        avgMiddle /= frames
        avgRing   /= frames
        avgLittle /= frames

        // Map label names to indices using the actual label_map.json
        let allLabels = labelMapper.allLabels
        func idx(_ name: String) -> Int? { allLabels.firstIndex(of: name) }

        if avgThumb < 0.3 && avgIndex < 0.3 && avgMiddle < 0.3 {
            if let i = idx("HELP") { scores[i] = 0.94 }
            if let i = idx("NEED") { scores[i] = 0.04 }
        } else if avgIndex > 0.6 && avgMiddle > 0.6 && avgRing < 0.3 {
            if let i = idx("WATER") { scores[i] = 0.91 }
            if let i = idx("I")    { scores[i] = 0.05 }
        } else if avgThumb > 0.6 && avgIndex > 0.6 && avgMiddle > 0.6 && avgRing > 0.6 && avgLittle > 0.6 {
            if let i = idx("HELLO")    { scores[i] = 0.88 }
            if let i = idx("THANK_YOU") { scores[i] = 0.08 }
        } else if avgIndex > 0.7 && avgMiddle < 0.3 {
            if let i = idx("I")   { scores[i] = 0.85 }
            if let i = idx("YOU") { scores[i] = 0.10 }
        } else if avgThumb < 0.3 && avgIndex > 0.5 {
            if let i = idx("NEED") { scores[i] = 0.89 }
            if let i = idx("WANT") { scores[i] = 0.06 }
        } else if avgMiddle > 0.5 && avgRing > 0.5 {
            if let i = idx("FOOD")     { scores[i] = 0.87 }
            if let i = idx("MEDICINE") { scores[i] = 0.08 }
        } else {
            if let i = idx("HELP") { scores[i] = 0.75 }
            if let i = idx("NEED") { scores[i] = 0.15 }
        }

        // Softmax normalization
        let maxVal = scores.max() ?? 1.0
        let expScores = scores.map { exp($0 - maxVal) }
        let sumExp = expScores.reduce(0, +)
        return expScores.map { $0 / sumExp }
    }
}
