import SwiftUI

public struct LearnSignsView: View {
    @EnvironmentObject var env: AppEnvironment
    @State private var searchText = ""
    @State private var selectedTutorial: TutorialItem?
    
    let columns = [
        GridItem(.flexible()),
        GridItem(.flexible())
    ]
    
    public init() {}
    
    var filteredTutorials: [TutorialItem] {
        if searchText.isEmpty {
            return env.tutorials
        } else {
            return env.tutorials.filter {
                $0.word.localizedCaseInsensitiveContains(searchText) ||
                $0.handshape.localizedCaseInsensitiveContains(searchText) ||
                $0.description.localizedCaseInsensitiveContains(searchText)
            }
        }
    }
    
    public var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: SBTheme.Spacing.medium) {
                SBGlassCard {
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Learn Sign Language 🤟")
                            .font(.headline)
                        Text("Master the 13 core vocabulary signs recognized by your SilentBridge glove.")
                            .font(.subheadline)
                            .foregroundColor(.secondary)
                    }
                }
                
                LazyVGrid(columns: columns, spacing: 14) {
                    ForEach(filteredTutorials) { tutorial in
                        Button {
                            selectedTutorial = tutorial
                        } label: {
                            VStack(alignment: .leading, spacing: 8) {
                                HStack {
                                    Text(tutorial.emoji)
                                        .font(.largeTitle)
                                    Spacer()
                                    Image(systemName: "play.circle.fill")
                                        .font(.title2)
                                        .foregroundColor(SBTheme.Colors.primary)
                                }
                                
                                Text(tutorial.word)
                                    .font(.headline.weight(.bold))
                                    .foregroundColor(.primary)
                                
                                Text(tutorial.handshape)
                                    .font(.caption)
                                    .foregroundColor(.secondary)
                                    .lineLimit(1)
                            }
                            .padding(SBTheme.Spacing.medium)
                            .background(SBTheme.Colors.glassFill)
                            .clipShape(RoundedRectangle(cornerRadius: SBTheme.Radius.large))
                            .overlay(
                                RoundedRectangle(cornerRadius: SBTheme.Radius.large)
                                    .stroke(SBTheme.Colors.cardBorder, lineWidth: 1)
                            )
                        }
                    }
                }
            }
            .padding(SBTheme.Spacing.medium)
        }
        .searchable(text: $searchText, prompt: "Search signs or handshapes...")
        .background(SBTheme.Colors.groupedBackground.ignoresSafeArea())
        .navigationTitle("Learn Signs")
        .navigationBarTitleDisplayMode(.inline)
        .sheet(item: $selectedTutorial) { tutorial in
            tutorialDetailSheet(tutorial)
        }
    }
    
    private func tutorialDetailSheet(_ item: TutorialItem) -> some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: SBTheme.Spacing.medium) {
                    HStack {
                        Text(item.emoji)
                            .font(.system(size: 60))
                        VStack(alignment: .leading, spacing: 4) {
                            Text(item.word)
                                .font(.largeTitle.weight(.bold))
                            SBStatusBadge(title: item.handshape, icon: "hand.raised.fill", color: SBTheme.Colors.primary)
                        }
                    }
                    .padding(.top, 8)
                    
                    VStack(alignment: .leading, spacing: 8) {
                        Text("How to Perform")
                            .font(.headline)
                        Text(item.description)
                            .font(.body)
                            .foregroundColor(.secondary)
                            .lineSpacing(4)
                    }
                    .padding()
                    .background(SBTheme.Colors.secondaryBackground)
                    .clipShape(RoundedRectangle(cornerRadius: SBTheme.Radius.medium))
                    
                    if let watchUrl = item.watchUrl {
                        Link(destination: watchUrl) {
                            HStack {
                                Image(systemName: "play.tv.fill")
                                Text("Watch Tutorial Video on YouTube")
                            }
                            .font(.headline)
                            .frame(maxWidth: .infinity)
                            .padding()
                            .background(Color.red)
                            .foregroundColor(.white)
                            .clipShape(RoundedRectangle(cornerRadius: SBTheme.Radius.medium))
                        }
                    }
                }
                .padding(SBTheme.Spacing.medium)
            }
            .navigationTitle("Sign Detail")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Close") { selectedTutorial = nil }
                }
            }
        }
    }
}
