import SwiftUI

@main
struct SilentBridgeApp: App {
    @StateObject private var env = AppEnvironment()
    
    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(env)
        }
    }
}
