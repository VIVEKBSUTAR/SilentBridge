import SwiftUI
import Combine

/// Central State Container and Real-Time Service Pipeline Orchestrator for SilentBridge.
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
    @Published public var packetRate: Double = 0.0
    
    // MARK: - Buffer & Sentence State
    @Published public var wordBuffer: [String] = []
    @Published public var formedSentence: String? = nil
    @Published public var translatedSentence: String? = nil
    @Published public var isFormingSentence: Bool = false
    
    // MARK: - Voice & TTS Settings
    @Published public var speechRate: Float = 0.5
    @Published public var speechPitch: Float = 1.0
    
    // MARK: - Data Models & Collections
    @Published public var modelLabels: [String] = []
    @Published public var customLabels: [String] = []
    @Published public var tutorials: [TutorialItem] = []
    @Published public var discoveredDevices: [BluetoothDevice] = []
    @Published public var feedbackCount: Int = 0
    
    // MARK: - Service Engines
    public let bluetoothManager = BluetoothManager()
    public let gestureEngine = GestureEngine()
    public let languageEngine = LanguageEngine()
    public let translationManager = TranslationManager()
    public let speechManager = SpeechManager()
    public let feedbackStore = FeedbackStore()
    private let labelMapper = LabelMapper()
    
    private var cancellables = Set<AnyCancellable>()
    
    public init() {
        setupPipeline()
        loadInitialData()
    }
    
    private func setupPipeline() {
        // 1. Observe Bluetooth Connection State
        bluetoothManager.$connectionState
            .receive(on: DispatchQueue.main)
            .sink { [weak self] state in
                guard let self = self else { return }
                self.connectionState = state
                if state == .connected {
                    self.gestureEngine.onBluetoothConnected()
                } else if state == .disconnected {
                    self.gestureEngine.onBluetoothDisconnected()
                }
            }
            .store(in: &cancellables)
        
        // 2. Observe Discovered Bluetooth Devices
        bluetoothManager.$discoveredDevices
            .receive(on: DispatchQueue.main)
            .sink { [weak self] devices in
                self?.discoveredDevices = devices
            }
            .store(in: &cancellables)
        
        // 3. Observe Telemetry Sensor Frames
        bluetoothManager.$latestFrame
            .receive(on: DispatchQueue.main)
            .sink { [weak self] frame in
                guard let self = self, let frame = frame else { return }
                self.latestSensorFrame = frame
                self.gestureEngine.onNewFrame(frame)
            }
            .store(in: &cancellables)
        
        bluetoothManager.$packetRate
            .receive(on: DispatchQueue.main)
            .sink { [weak self] rate in
                self?.packetRate = rate
            }
            .store(in: &cancellables)
        
        // 4. Observe Gesture Engine Inference State
        gestureEngine.$state
            .receive(on: DispatchQueue.main)
            .sink { [weak self] state in
                self?.inferenceState = state
            }
            .store(in: &cancellables)
        
        // 5. Observe Gesture Engine Prediction Output
        gestureEngine.$result
            .receive(on: DispatchQueue.main)
            .sink { [weak self] res in
                guard let self = self, let res = res else {
                    self?.gestureResult = nil
                    return
                }
                let adjusted = self.feedbackStore.applyPenalty(gestureName: res.gestureName, rawConfidence: res.confidence)
                self.gestureResult = GestureResult(
                    gestureName: res.gestureName,
                    confidence: res.confidence,
                    adjustedConfidence: adjusted,
                    topPredictions: res.topPredictions,
                    frames: res.frames
                )
            }
            .store(in: &cancellables)
        
        // 6. Setup Auto-Loop Gesture Decision Callback
        gestureEngine.onAutoGestureResult = { [weak self] result in
            guard let self = self else { return false }
            let adjusted = self.feedbackStore.applyPenalty(gestureName: result.gestureName, rawConfidence: result.confidence)
            if adjusted >= CaptureMode.autoConfidenceThreshold {
                Task { @MainActor in
                    self.addWordToBuffer(result.gestureName)
                    self.autoAcceptedCount += 1
                }
                return true
            }
            return false
        }
    }
    
    private func loadInitialData() {
        self.modelLabels = labelMapper.allLabels
        self.tutorials = TutorialRepository.tutorials
        self.customLabels = UserDefaults.standard.stringArray(forKey: "sb_custom_labels") ?? []
        self.triggerMode = UserDefaults.standard.string(forKey: "sb_trigger_mode") ?? "manual"
        updateFeedbackCount()
    }
    
    // MARK: - Bluetooth Actions
    
    public func startScanning() {
        bluetoothManager.startScanning()
    }
    
    public func refreshDevices() {
        bluetoothManager.startScanning()
    }
    
    public func connectDevice(address: String) {
        bluetoothManager.connect(to: address)
    }
    
    public func disconnectDevice() {
        bluetoothManager.disconnect()
    }
    
    // MARK: - Gesture Session & Mode Controls
    
    public func setCaptureMode(_ mode: CaptureMode) {
        self.captureMode = mode
        self.autoAcceptedCount = 0
        gestureEngine.stopSession()
        if mode == .auto && connectionState.isConnected {
            gestureEngine.startAutoLoop()
        } else if connectionState.isConnected {
            gestureEngine.startSession()
        }
    }
    
    public func startGestureCapture() {
        if captureMode == .auto {
            self.autoAcceptedCount = 0
            gestureEngine.startAutoLoop()
        } else {
            gestureEngine.startSession()
        }
    }
    
    public func stopAutoCapture() {
        gestureEngine.stopAutoLoop()
    }
    
    public func onFeedbackYes() {
        guard let result = gestureResult else { return }
        addWordToBuffer(result.gestureName)
        feedbackStore.recordFeedback(gestureName: result.gestureName, isCorrect: true)
        updateFeedbackCount()
        self.gestureResult = nil
        gestureEngine.resetEngine()
    }
    
    public func onFeedbackNo() {
        guard let result = gestureResult else { return }
        feedbackStore.recordFeedback(gestureName: result.gestureName, isCorrect: false)
        updateFeedbackCount()
        self.gestureResult = nil
        gestureEngine.resetEngine()
    }
    
    // MARK: - Word Buffer & Sentence Reconstruction
    
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
            let sentence = await languageEngine.reconstructSentence(tokens: wordBuffer)
            self.formedSentence = sentence
            self.isFormingSentence = false
            await translateAndAutoSpeak(sentence: sentence)
        }
    }
    
    private func translateAndAutoSpeak(sentence: String) async {
        let translated = await translationManager.translate(text: sentence, targetLanguage: selectedLanguage)
        self.translatedSentence = translated
        speechManager.speak(text: translated, language: selectedLanguage, rate: speechRate, pitch: speechPitch)
    }
    
    public func setTargetLanguage(_ lang: SupportedLanguage) {
        self.selectedLanguage = lang
        if let sentence = formedSentence {
            Task {
                await translateAndAutoSpeak(sentence: sentence)
            }
        }
    }
    
    public func speakCurrentSentence() {
        guard let text = translatedSentence ?? formedSentence else { return }
        speechManager.speak(text: text, language: selectedLanguage, rate: speechRate, pitch: speechPitch)
    }
    
    public func clearSentence() {
        self.formedSentence = nil
        self.translatedSentence = nil
    }
    
    // MARK: - Custom Dictionary Management
    
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
    
    public func getStats() -> [String: (correct: Int, wrong: Int)] {
        feedbackStore.getStats()
    }
    
    private func updateFeedbackCount() {
        let stats = feedbackStore.getStats()
        self.feedbackCount = stats.values.reduce(0) { $0 + $1.correct + $1.wrong }
    }
    
    public func exportDataset() {
        // Exports JSON feedback samples
    }
}
