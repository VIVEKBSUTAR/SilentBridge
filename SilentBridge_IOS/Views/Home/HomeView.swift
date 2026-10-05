import SwiftUI

public struct HomeView: View {
    @EnvironmentObject var env: AppEnvironment
    @State private var showLanguagePicker = false
    
    public init() {}
    
    public var body: some View {
        ScrollView {
            VStack(spacing: SBTheme.Spacing.medium) {
                // MARK: 1. Connection & Mode Bar
                connectionAndModeHeader
                
                // MARK: 2. Recognized Gesture Display
                gestureRecognitionCard
                
                // MARK: 3. Word Buffer
                wordBufferCard
                
                // MARK: 4. Formed Sentence Card
                formedSentenceCard
            }
            .padding(.horizontal, SBTheme.Spacing.medium)
            .padding(.vertical, SBTheme.Spacing.small)
        }
        .background(SBTheme.Colors.groupedBackground.ignoresSafeArea())
        .navigationTitle("SilentBridge")
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .navigationBarLeading) {
                Button {
                    showLanguagePicker = true
                } label: {
                    HStack(spacing: 4) {
                        Image(systemName: "translate")
                        Text(env.selectedLanguage.displayName)
                            .font(.caption.weight(.bold))
                    }
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .background(SBTheme.Colors.primary.opacity(0.12))
                    .clipShape(Capsule())
                }
            }
            
            ToolbarItem(placement: .navigationBarTrailing) {
                Menu {
                    Button {
                        env.navigationPath.append(AppRoute.connection)
                    } label: {
                        Label("Glove Connection", systemImage: "antenna.radiowaves.left.and.right")
                    }
                    
                    Button {
                        env.navigationPath.append(AppRoute.statistics)
                    } label: {
                        Label("Prediction Stats", systemImage: "chart.bar.fill")
                    }
                    
                    Button {
                        env.navigationPath.append(AppRoute.diagnostics)
                    } label: {
                        Label("Diagnostics Telemetry", systemImage: "cpu")
                    }
                    
                    Button {
                        env.navigationPath.append(AppRoute.manageWords)
                    } label: {
                        Label("Manage Words", systemImage: "character.book.closed.fill")
                    }
                    
                    Button {
                        env.navigationPath.append(AppRoute.learnSigns)
                    } label: {
                        Label("Learn Signs 🤟", systemImage: "hand.raised.fill")
                    }
                    
                    Divider()
                    
                    Button {
                        env.navigationPath.append(AppRoute.settings)
                    } label: {
                        Label("Settings", systemImage: "gearshape.fill")
                    }
                } label: {
                    Image(systemName: "ellipsis.circle.fill")
                        .font(.title3)
                }
            }
        }
        .sheet(isPresented: $showLanguagePicker) {
            languageSelectionSheet
        }
    }
    
    // MARK: - Header
    private var connectionAndModeHeader: some View {
        SBGlassCard {
            HStack {
                // Connection Indicator
                Button {
                    env.navigationPath.append(AppRoute.connection)
                } label: {
                    HStack(spacing: 8) {
                        Circle()
                            .fill(env.connectionState.isConnected ? SBTheme.Colors.success : SBTheme.Colors.danger)
                            .frame(width: 10, height: 10)
                        
                        VStack(alignment: .leading, spacing: 2) {
                            Text("ESP32 Glove")
                                .font(.caption2)
                                .foregroundColor(.secondary)
                            Text(env.connectionState.rawValue)
                                .font(.subheadline.weight(.semibold))
                                .foregroundColor(.primary)
                        }
                    }
                }
                
                Spacer()
                
                // Mode Toggle Segment
                Picker("Capture Mode", selection: Binding(
                    get: { env.captureMode },
                    set: { env.setCaptureMode($0) }
                )) {
                    ForEach(CaptureMode.allCases) { mode in
                        Label(mode.title, systemImage: mode.iconName)
                            .tag(mode)
                    }
                }
                .pickerStyle(.segmented)
                .frame(maxWidth: 160)
            }
        }
    }
    
    // MARK: - Recognition Display Card
    private var gestureRecognitionCard: some View {
        SBGlassCard {
            VStack(spacing: SBTheme.Spacing.small) {
                HStack {
                    SBStatusBadge(
                        title: env.inferenceState.userFriendlyText,
                        icon: env.captureMode.iconName,
                        color: env.inferenceState == .recording ? SBTheme.Colors.warning : SBTheme.Colors.primary
                    )
                    Spacer()
                    if env.captureMode == .auto && env.autoAcceptedCount > 0 {
                        Text("\(env.autoAcceptedCount) accepted")
                            .font(.caption.weight(.bold))
                            .foregroundColor(SBTheme.Colors.success)
                    }
                }
                
                // Big Gesture Result
                if let result = env.gestureResult {
                    VStack(spacing: 4) {
                        Text(result.gestureName)
                            .font(.system(size: 42, weight: .bold, design: .rounded))
                            .foregroundColor(SBTheme.Colors.primary)
                        
                        Text("Confidence: \(Int(result.adjustedConfidence * 100))%")
                            .font(.subheadline.weight(.medium))
                            .foregroundColor(.secondary)
                    }
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 8)
                } else {
                    VStack(spacing: 8) {
                        Image(systemName: "hand.raised.palm.fill")
                            .font(.system(size: 36))
                            .foregroundColor(.secondary.opacity(0.5))
                        Text("Perform a gesture with the glove")
                            .font(.subheadline)
                            .foregroundColor(.secondary)
                    }
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 16)
                }
                
                // Controls
                if env.captureMode == .manual {
                    HStack(spacing: SBTheme.Spacing.small) {
                        if env.inferenceState == .resultFrozen {
                            SBPrimaryButton(title: "Correct (Yes)", icon: "checkmark", color: SBTheme.Colors.success) {
                                env.onFeedbackYes()
                            }
                            SBPrimaryButton(title: "Wrong (No)", icon: "xmark", color: SBTheme.Colors.danger) {
                                env.onFeedbackNo()
                            }
                        } else {
                            SBPrimaryButton(
                                title: env.inferenceState == .recording ? "Recording..." : "Start Capture",
                                icon: "play.fill",
                                isLoading: env.inferenceState == .recording
                            ) {
                                env.startGestureCapture()
                            }
                        }
                    }
                } else {
                    // Auto Mode control
                    HStack {
                        if env.inferenceState == .recording {
                            SBPrimaryButton(title: "Stop Auto Loop", icon: "stop.fill", color: SBTheme.Colors.danger) {
                                env.stopAutoCapture()
                            }
                        } else {
                            SBPrimaryButton(title: "Start Auto Loop", icon: "arrow.clockwise.circle.fill") {
                                env.startGestureCapture()
                            }
                        }
                    }
                }
            }
        }
    }
    
    // MARK: - Word Buffer Card
    private var wordBufferCard: some View {
        SBGlassCard {
            VStack(alignment: .leading, spacing: SBTheme.Spacing.small) {
                HStack {
                    Text("Word Buffer (\(env.wordBuffer.count))")
                        .font(.headline)
                    Spacer()
                    if !env.wordBuffer.isEmpty {
                        Button("Clear") {
                            env.clearBuffer()
                        }
                        .font(.subheadline.weight(.semibold))
                        .foregroundColor(SBTheme.Colors.danger)
                    }
                }
                
                if env.wordBuffer.isEmpty {
                    Text("Recognized words will accumulate here to form sentences.")
                        .font(.footnote)
                        .foregroundColor(.secondary)
                        .padding(.vertical, 8)
                } else {
                    ScrollView(.horizontal, showsIndicators: false) {
                        HStack(spacing: 8) {
                            ForEach(Array(env.wordBuffer.enumerated()), id: \.offset) { index, word in
                                SBGesturePill(word: word) {
                                    env.removeWordFromBuffer(at: index)
                                }
                            }
                        }
                    }
                    
                    SBPrimaryButton(
                        title: "Form Sentence",
                        icon: "sparkles",
                        isLoading: env.isFormingSentence,
                        color: SBTheme.Colors.primary
                    ) {
                        env.triggerSentenceFormation()
                    }
                    .padding(.top, 4)
                }
            }
        }
    }
    
    // MARK: - Formed Sentence Card
    private var formedSentenceCard: some View {
        VStack {
            if let sentence = env.formedSentence {
                SBGlassCard {
                    VStack(alignment: .leading, spacing: SBTheme.Spacing.small) {
                        HStack {
                            Label("Reconstructed Sentence", systemImage: "quote.bubble.fill")
                                .font(.caption.weight(.bold))
                                .foregroundColor(SBTheme.Colors.primary)
                            Spacer()
                            Button {
                                env.clearSentence()
                            } label: {
                                Image(systemName: "xmark.circle.fill")
                                    .foregroundColor(.secondary)
                            }
                        }
                        
                        Text(sentence)
                            .font(.title3.weight(.semibold))
                            .foregroundColor(.primary)
                        
                        if let translated = env.translatedSentence, env.selectedLanguage != .english {
                            VStack(alignment: .leading, spacing: 4) {
                                Text(env.selectedLanguage.displayName)
                                    .font(.caption2.weight(.bold))
                                    .foregroundColor(.secondary)
                                Text(translated)
                                    .font(.headline)
                                    .foregroundColor(SBTheme.Colors.primaryAccent)
                            }
                            .padding(10)
                            .background(SBTheme.Colors.primary.opacity(0.08))
                            .clipShape(RoundedRectangle(cornerRadius: SBTheme.Radius.small))
                        }
                        
                        HStack(spacing: SBTheme.Spacing.small) {
                            SBPrimaryButton(title: "Speak", icon: "speaker.wave.2.fill") {
                                env.speakCurrentSentence()
                            }
                            
                            SBSecondaryButton(title: "Copy", icon: "doc.on.doc") {
                                UIPasteboard.general.string = env.translatedSentence ?? sentence
                            }
                        }
                        .padding(.top, 4)
                    }
                }
            }
        }
    }
    
    // MARK: - Language Selector Sheet
    private var languageSelectionSheet: some View {
        NavigationStack {
            List(SupportedLanguage.allCases) { lang in
                Button {
                    env.setTargetLanguage(lang)
                    showLanguagePicker = false
                } label: {
                    HStack {
                        VStack(alignment: .leading) {
                            Text(lang.displayName)
                                .font(.headline)
                            Text(lang.nativeName)
                                .font(.subheadline)
                                .foregroundColor(.secondary)
                        }
                        Spacer()
                        if env.selectedLanguage == lang {
                            Image(systemName: "checkmark")
                                .foregroundColor(SBTheme.Colors.primary)
                                .font(.headline)
                        }
                    }
                }
            }
            .navigationTitle("Select Language")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Done") { showLanguagePicker = false }
                }
            }
        }
    }
}
