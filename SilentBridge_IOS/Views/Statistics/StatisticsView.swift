import SwiftUI

public struct StatisticsView: View {
    @EnvironmentObject var env: AppEnvironment
    
    public init() {}
    
    public var body: some View {
        List {
            Section {
                HStack {
                    VStack(alignment: .leading) {
                        Text("Total Logged Sample Feedbacks")
                            .font(.subheadline)
                            .foregroundColor(.secondary)
                        Text("\(env.feedbackCount)")
                            .font(.system(size: 32, weight: .bold))
                            .foregroundColor(SBTheme.Colors.primary)
                    }
                    Spacer()
                    Image(systemName: "chart.line.uptrend.xyaxis.circle.fill")
                        .font(.system(size: 44))
                        .foregroundColor(SBTheme.Colors.primary.opacity(0.8))
                }
                .padding(.vertical, 8)
            } header: {
                Text("Overview")
            }
            
            Section {
                let stats = env.getStats()
                if stats.isEmpty {
                    Text("No gesture feedback logged yet. Use Manual mode to verify gesture predictions.")
                        .font(.footnote)
                        .foregroundColor(.secondary)
                        .padding(.vertical, 8)
                } else {
                    ForEach(stats.sorted(by: { $0.key < $1.key }), id: \.key) { gesture, pair in
                        let correct = pair.0
                        let wrong = pair.1
                        let total = correct + wrong
                        let accuracy = total > 0 ? (Double(correct) / Double(total) * 100) : 100.0
                        
                        VStack(alignment: .leading, spacing: 6) {
                            HStack {
                                Text(gesture)
                                    .font(.headline)
                                Spacer()
                                Text(String(format: "%.0f%% Acc", accuracy))
                                    .font(.subheadline.weight(.bold))
                                    .foregroundColor(accuracy >= 80 ? SBTheme.Colors.success : SBTheme.Colors.warning)
                            }
                            
                            HStack {
                                ProgressView(value: accuracy, total: 100)
                                    .tint(accuracy >= 80 ? SBTheme.Colors.success : SBTheme.Colors.warning)
                                Text("\(correct) correct / \(wrong) wrong")
                                    .font(.caption)
                                    .foregroundColor(.secondary)
                            }
                        }
                        .padding(.vertical, 4)
                    }
                }
            } header: {
                Text("Gesture Accuracy Stats")
            }
        }
        .navigationTitle("Prediction Stats")
        .navigationBarTitleDisplayMode(.inline)
    }
}
