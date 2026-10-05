import SwiftUI

struct ContentView: View {
    @EnvironmentObject var env: AppEnvironment
    
    var body: some View {
        NavigationStack(path: $env.navigationPath) {
            HomeView()
                .navigationDestination(for: AppRoute.self) { route in
                    switch route {
                    case .connection:
                        ConnectionView()
                    case .diagnostics:
                        DiagnosticsView()
                    case .statistics:
                        StatisticsView()
                    case .manageWords:
                        ManageWordsView()
                    case .settings:
                        SettingsView()
                    case .learnSigns:
                        LearnSignsView()
                    case .manualMode:
                        ManualModeView()
                    }
                }
        }
        .accentColor(SBTheme.Colors.primary)
    }
}

#Preview {
    ContentView()
        .environmentObject(AppEnvironment())
}
