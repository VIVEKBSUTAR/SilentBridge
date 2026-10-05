import SwiftUI
import Combine

/// Core State Container and Dependency Environment for SilentBridge iOS application.
@MainActor
public final class AppEnvironment: ObservableObject {
    
    // MARK: - Navigation State
    @Published public var navigationPath = NavigationPath()
    
    // MARK: - App & Connection State
    @Published public var connectionState: ConnectionState = .disconnected
    @Published public var inferenceState: InferenceState = .disconnected
    @Published public var captureMode: CaptureMode = .manual
    @Published public var selectedLanguage: SupportedLanguage = .english
    @Published public var triggerMode: String = "manual"
    
    // MARK: - Sensor & ML Telemetry State
    @Published public var latestSensorFrame: SensorFrame? = nil
    @Published public var gestureResult: GestureResult? = nil
    @Published public var autoAcceptedCount: Int = 0
    
    // MARK: - Buffer & Sentence State
    @Published public var wordBuffer: [String] = []
    @Published public var formedSentence: String? = nil
    @Published public var translatedSentence: String? = nil
    @Published public var isFormingSentence: Bool = false
    
    // MARK: - Voice & TTS Settings
    @Published public var speechRate: Float = 0.5
    @Published public var speechPitch: Float = 1.0
    
    // MARK: - Dictionaries & Tutorials Data
    @Published public var modelLabels: [String] = [
        "ALL", "FOOD", "HELLO", "HELP", "I",
        "MEDICINE", "NEED", "NO", "THANK_YOU",
        "WANT", "WATER", "YES", "YOU"
    ]
    @Published public var customLabels: [String] = []
    @Published public var tutorials: [TutorialItem] = []
    @Published public var discoveredDevices: [BluetoothDevice] = []
    @Published public var feedbackCount: Int = 0
    
    private var feedbackHistory: [String: (correct: Int, wrong: Int)] = [:]
    
    public init() {
        loadInitialData()
    }
    
    private func loadInitialData() {
        self.tutorials = TutorialRepository.tutorials
        self.customLabels = UserDefaults.standard.stringArray(forKey: "sb_custom_labels") ?? []
        self.triggerMode = UserDefaults.standard.string(forKey: "sb_trigger_mode") ?? "manual"
        
        // Mock discovered glove device for Phase 1 UI preview
        self.discoveredDevices = [
            BluetoothDevice(name: "SilentBridge ESP32 Glove", address: "ESP32-SB-GLOVE-01", rssi: -48, isConnected: false)
        ]
    }
    
    // MARK: - User Actions & Handlers
    
    public func setCaptureMode(_ mode: CaptureMode) {
        self.captureMode = mode
        self.autoAcceptedCount = 0
        if mode == .auto && connectionState.isConnected {
            self.inferenceState = .recording
        } else if connectionState.isConnected {
            self.inferenceState = .ready
        }
    }
    
    public func setTargetLanguage(_ lang: SupportedLanguage) {
        self.selectedLanguage = lang
        if let sentence = formedSentence {
            translateCurrentSentence(sentence)
        }
    }
    
    public func setTriggerMode(_ mode: String) {
        self.triggerMode = mode
        UserDefaults.standard.set(mode, forKey: "sb_trigger_mode")
    }
    
    public func setSpeechRate(_ rate: Float) {
        self.speechRate = rate
    }
    
    public func setSpeechPitch(_ pitch: Float) {
        self.speechPitch = pitch
    }
    
    public func connectDevice(address: String) {
        self.connectionState = .connecting
        Task {
            try? await Task.sleep(nanoseconds: 800_000_000)
            self.connectionState = .connected
            self.inferenceState = .ready
            if let idx = discoveredDevices.firstIndex(where: { $0.address == address }) {
                discoveredDevices[idx].isConnected = true
            }
        }
    }
    
    public func disconnectDevice() {
        self.connectionState = .disconnected
        self.inferenceState = .disconnected
        for i in 0..<discoveredDevices.count {
            discoveredDevices[i].isConnected = false
        }
    }
    
    public func refreshDevices() {
        // Will trigger CoreBluetooth scan in Phase 2
    }
    
    public func startGestureCapture() {
        guard connectionState.isConnected else { return }
        if captureMode == .manual {
            self.inferenceState = .recording
            Task {
                try? await Task.sleep(nanoseconds: 1_200_000_000)
                self.inferenceState = .modelInference
                try? await Task.sleep(nanoseconds: 300_000_000)
                let sampleResult = GestureResult(
                    gestureName: modelLabels.randomElement() ?? "HELP",
                    confidence: 0.92,
                    topPredictions: [("HELP", 0.92), ("NEED", 0.05), ("WATER", 0.03)]
                )
                self.gestureResult = sampleResult
                self.inferenceState = .resultFrozen
            }
        } else {
            self.autoAcceptedCount = 0
            self.inferenceState = .recording
        }
    }
    
    public func stopAutoCapture() {
        self.inferenceState = .ready
    }
    
    public func onFeedbackYes() {
        guard let result = gestureResult else { return }
        addWordToBuffer(result.gestureName)
        recordFeedback(gesture: result.gestureName, isCorrect: true)
        self.gestureResult = nil
        self.inferenceState = .ready
    }
    
    public func onFeedbackNo() {
        guard let result = gestureResult else { return }
        recordFeedback(gesture: result.gestureName, isCorrect: false)
        self.gestureResult = nil
        self.inferenceState = .ready
    }
    
    public func addWordToBuffer(_ word: String) {
        wordBuffer.append(word)
    }
    
    public func removeWordFromBuffer(at index: Int) {
        guard index >= 0 && index < wordBuffer.count else { return }
        wordBuffer.remove(at: index)
    }
    
    public func clearBuffer() {
        wordBuffer.removeAll()
    }
    
    public func triggerSentenceFormation() {
        guard !wordBuffer.isEmpty else { return }
        isFormingSentence = true
        Task {
            try? await Task.sleep(nanoseconds: 600_000_000)
            let result = reconstructSentenceFallback(tokens: wordBuffer)
            self.formedSentence = result
            self.isFormingSentence = false
            translateCurrentSentence(result)
        }
    }
    
    private func translateCurrentSentence(_ text: String) {
        if selectedLanguage == .english {
            self.translatedSentence = text
        } else {
            // Simplified translation representation for UI flow
            self.translatedSentence = "[\(selectedLanguage.displayName)] \(text)"
        }
    }
    
    public func speakCurrentSentence() {
        // Will connect to AVSpeechSynthesizer in SpeechManager
    }
    
    public func clearSentence() {
        self.formedSentence = nil
        self.translatedSentence = nil
    }
    
    public func addCustomWord(_ word: String) {
        let clean = word.trimmingCharacters(in: .whitespacesAndNewlines).uppercased()
        guard !clean.isEmpty, !customLabels.contains(clean) else { return }
        customLabels.append(clean)
        UserDefaults.standard.set(customLabels, forKey: "sb_custom_labels")
    }
    
    public func removeCustomWord(_ word: String) {
        customLabels.removeAll { $0 == word.uppercased() }
        UserDefaults.standard.set(customLabels, forKey: "sb_custom_labels")
    }
    
    public func recordFeedback(gesture: String, isCorrect: Bool) {
        var current = feedbackHistory[gesture] ?? (0, 0)
        if isCorrect {
            current.correct += 1
        } else {
            current.wrong += 1
        }
        feedbackHistory[gesture] = current
        feedbackCount += 1
    }
    
    public func getStats() -> [String: (Int, Int)] {
        feedbackHistory
    }
    
    public func exportDataset() {
        // Exports logged samples
    }
    
    private func reconstructSentenceFallback(tokens: [String]) -> String {
        let upper = tokens.map { $0.uppercased() }
        let hasHelp = upper.contains("HELP")
        let hasWater = upper.contains("WATER")
        let hasFood = upper.contains("FOOD")
        let hasMedicine = upper.contains("MEDICINE")
        let hasNeed = upper.contains("NEED") || upper.contains("WANT")
        
        if hasHelp {
            return "Please help me!"
        } else if hasNeed && hasWater {
            return "I need water."
        } else if hasNeed && hasFood {
            return "I want food."
        } else if hasNeed && hasMedicine {
            return "I need medicine urgently."
        } else {
            let joined = tokens.joined(separator: " ").lowercased()
            return joined.capitalized + "."
        }
    }
}
