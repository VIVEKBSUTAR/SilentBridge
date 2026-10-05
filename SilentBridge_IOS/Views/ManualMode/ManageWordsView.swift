import SwiftUI

public struct ManageWordsView: View {
    @EnvironmentObject var env: AppEnvironment
    @State private var newWordText: String = ""
    
    public init() {}
    
    public var body: some View {
        List {
            Section {
                HStack {
                    TextField("New Gesture Word (e.g. HELP_ME)", text: $newWordText)
                        .autocapitalization(.allCharacters)
                        .disableAutocorrection(true)
                    
                    Button("Add") {
                        if !newWordText.trimmingCharacters(in: .whitespaces).isEmpty {
                            env.addCustomWord(newWordText)
                            newWordText = ""
                        }
                    }
                    .font(.headline)
                    .disabled(newWordText.trimmingCharacters(in: .whitespaces).isEmpty)
                }
            } header: {
                Text("Add Custom Gesture Word")
            } footer: {
                Text("Custom words are added to your personal vocabulary dictionary and recognized during sentence formation.")
            }
            
            Section {
                ForEach(env.customLabels, id: \.self) { word in
                    HStack {
                        Text(word)
                            .font(.headline)
                        Spacer()
                        Button {
                            env.removeCustomWord(word)
                        } label: {
                            Image(systemName: "trash")
                                .foregroundColor(SBTheme.Colors.danger)
                        }
                    }
                }
            } header: {
                Text("Custom Dictionary (\(env.customLabels.count))")
            }
            
            Section {
                ForEach(env.modelLabels, id: \.self) { word in
                    Text(word)
                        .font(.body)
                        .foregroundColor(.secondary)
                }
            } header: {
                Text("Model Standard Classes (\(env.modelLabels.count))")
            }
        }
        .navigationTitle("Manage Words")
        .navigationBarTitleDisplayMode(.inline)
    }
}
