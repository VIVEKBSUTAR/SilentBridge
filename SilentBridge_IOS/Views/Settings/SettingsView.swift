import SwiftUI

public struct SettingsView: View {
    @EnvironmentObject var env: AppEnvironment
    
    public init() {}
    
    public var body: some View {
        List {
            Section {
                Picker("Output Language", selection: Binding(
                    get: { env.selectedLanguage },
                    set: { env.setTargetLanguage($0) }
                )) {
                    ForEach(SupportedLanguage.allCases) { lang in
                        Text("\(lang.displayName) (\(lang.nativeName))")
                            .tag(lang)
                    }
                }
            } header: {
                Text("Language & Translation")
            } footer: {
                Text("Translations are generated locally on-device for supported languages.")
            }
            
            Section {
                Picker("Capture Mode", selection: Binding(
                    get: { env.captureMode },
                    set: { env.setCaptureMode($0) }
                )) {
                    ForEach(CaptureMode.allCases) { mode in
                        Label(mode.title, systemImage: mode.iconName)
                            .tag(mode)
                    }
                }
                
                Picker("Sentence Trigger Mode", selection: Binding(
                    get: { env.triggerMode },
                    set: { env.setTriggerMode($0) }
                )) {
                    Text("Manual Button").tag("manual")
                    Text("Auto (5s Inactivity)").tag("auto")
                }
            } header: {
                Text("Recognition & Controls")
            }
            
            Section {
                HStack {
                    Text("Speech Rate")
                    Spacer()
                    Slider(value: Binding(
                        get: { env.speechRate },
                        set: { env.setSpeechRate($0) }
                    ), in: 0.2...0.8, step: 0.05)
                    .frame(width: 140)
                }
                
                HStack {
                    Text("Speech Pitch")
                    Spacer()
                    Slider(value: Binding(
                        get: { env.speechPitch },
                        set: { env.setSpeechPitch($0) }
                    ), in: 0.5...1.5, step: 0.1)
                    .frame(width: 140)
                }
                
                Button("Test Speech") {
                    env.speakCurrentSentence()
                }
            } header: {
                Text("Text-To-Speech Output")
            }
            
            Section {
                HStack {
                    Text("Recorded Feedback Samples")
                    Spacer()
                    Text("\(env.feedbackCount)")
                        .foregroundColor(.secondary)
                        .fontWeight(.bold)
                }
                
                Button {
                    env.exportDataset()
                } label: {
                    Label("Export Dataset (JSON)", systemImage: "square.and.arrow.up")
                }
            } header: {
                Text("Feedback & Training Data")
            }
            
            Section {
                HStack {
                    Text("Version")
                    Spacer()
                    Text("1.0.0 (Native iOS)")
                        .foregroundColor(.secondary)
                }
                HStack {
                    Text("Model Architecture")
                    Spacer()
                    Text("BiLSTM (100x13)")
                        .foregroundColor(.secondary)
                }
                HStack {
                    Text("Device Hardware")
                    Spacer()
                    Text("ESP32 Wearable Glove")
                        .foregroundColor(.secondary)
                }
            } header: {
                Text("About SilentBridge")
            }
        }
        .navigationTitle("Settings")
        .navigationBarTitleDisplayMode(.inline)
    }
}
