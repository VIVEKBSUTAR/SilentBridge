import SwiftUI

public struct ManualModeView: View {
    @EnvironmentObject var env: AppEnvironment
    
    let columns = [
        GridItem(.flexible()),
        GridItem(.flexible()),
        GridItem(.flexible())
    ]
    
    public init() {}
    
    public var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: SBTheme.Spacing.medium) {
                SBGlassCard {
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Manual Gesture Input")
                            .font(.headline)
                        Text("Tap any gesture below to add it directly to the active word buffer.")
                            .font(.subheadline)
                            .foregroundColor(.secondary)
                    }
                }
                
                Text("Standard Vocabulary (\(env.modelLabels.count))")
                    .font(.headline)
                    .padding(.horizontal, 4)
                
                LazyVGrid(columns: columns, spacing: 12) {
                    ForEach(env.modelLabels, id: \.self) { label in
                        Button {
                            env.addWordToBuffer(label)
                        } label: {
                            VStack(spacing: 6) {
                                Text(label)
                                    .font(.subheadline.weight(.bold))
                                    .foregroundColor(.primary)
                                Image(systemName: "plus.circle.fill")
                                    .font(.caption)
                                    .foregroundColor(SBTheme.Colors.primary)
                            }
                            .frame(maxWidth: .infinity)
                            .padding(.vertical, 16)
                            .background(SBTheme.Colors.glassFill)
                            .clipShape(RoundedRectangle(cornerRadius: SBTheme.Radius.medium))
                            .overlay(
                                RoundedRectangle(cornerRadius: SBTheme.Radius.medium)
                                    .stroke(SBTheme.Colors.cardBorder, lineWidth: 1)
                            )
                        }
                    }
                }
                
                if !env.customLabels.isEmpty {
                    Text("Custom Gestures (\(env.customLabels.count))")
                        .font(.headline)
                        .padding(.top, 16)
                        .padding(.horizontal, 4)
                    
                    LazyVGrid(columns: columns, spacing: 12) {
                        ForEach(env.customLabels, id: \.self) { label in
                            Button {
                                env.addWordToBuffer(label)
                            } label: {
                                VStack(spacing: 6) {
                                    Text(label)
                                        .font(.subheadline.weight(.bold))
                                        .foregroundColor(SBTheme.Colors.primaryAccent)
                                    Image(systemName: "star.fill")
                                        .font(.caption)
                                        .foregroundColor(SBTheme.Colors.warning)
                                }
                                .frame(maxWidth: .infinity)
                                .padding(.vertical, 16)
                                .background(SBTheme.Colors.primary.opacity(0.08))
                                .clipShape(RoundedRectangle(cornerRadius: SBTheme.Radius.medium))
                            }
                        }
                    }
                }
            }
            .padding(SBTheme.Spacing.medium)
        }
        .background(SBTheme.Colors.groupedBackground.ignoresSafeArea())
        .navigationTitle("Manual Input")
        .navigationBarTitleDisplayMode(.inline)
    }
}
