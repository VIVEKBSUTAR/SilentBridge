import Foundation

/// Capture mode for gesture processing: Manual tap vs Auto hands-free continuous loop.
public enum CaptureMode: String, Codable, Sendable, CaseIterable, Identifiable {
    case manual = "MANUAL"
    case auto = "AUTO"
    
    public var id: String { rawValue }
    
    public var title: String {
        switch self {
        case .manual: return "Manual Mode"
        case .auto: return "Auto Loop Mode"
        }
    }
    
    public var iconName: String {
        switch self {
        case .manual: return "hand.tap.fill"
        case .auto: return "arrow.triangle.2.circlepath.circle.fill"
        }
    }
    
    public var subtitle: String {
        switch self {
        case .manual: return "Tap start for each gesture. Freeze and confirm predictions."
        case .auto: return "Continuous hands-free recognition with confidence filtering."
        }
    }
    
    public static let autoConfidenceThreshold: Float = 0.55
}
