import SwiftUI

/// Navigation destinations in SilentBridge navigation hierarchy.
public enum AppRoute: Hashable, Identifiable {
    case connection
    case diagnostics
    case statistics
    case manageWords
    case settings
    case learnSigns
    case manualMode
    
    public var id: String {
        switch self {
        case .connection: return "connection"
        case .diagnostics: return "diagnostics"
        case .statistics: return "statistics"
        case .manageWords: return "manageWords"
        case .settings: return "settings"
        case .learnSigns: return "learnSigns"
        case .manualMode: return "manualMode"
        }
    }
}
