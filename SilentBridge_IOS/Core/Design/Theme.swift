import SwiftUI

/// Semantic Design System Theme for SilentBridge iOS.
/// Built following HIG principles for accessibility, visual clarity, high contrast, and dynamic type support.
public enum SBTheme {
    
    // MARK: - Color Palette
    public enum Colors {
        public static let primary = Color(red: 0.0, green: 0.48, blue: 1.0) // iOS System Blue
        public static let primaryAccent = Color(red: 0.2, green: 0.6, blue: 1.0)
        public static let success = Color(red: 0.15, green: 0.78, blue: 0.35)
        public static let warning = Color(red: 1.0, green: 0.62, blue: 0.04)
        public static let danger = Color(red: 1.0, green: 0.23, blue: 0.19)
        public static let emergencyBackground = Color(red: 0.45, green: 0.05, blue: 0.05)
        
        public static let background = Color(uiColor: .systemBackground)
        public static let secondaryBackground = Color(uiColor: .secondarySystemBackground)
        public static let tertiaryBackground = Color(uiColor: .tertiarySystemBackground)
        public static let groupedBackground = Color(uiColor: .systemGroupedBackground)
        
        public static let cardBorder = Color.primary.opacity(0.12)
        public static let glassFill = Color(uiColor: .secondarySystemGroupedBackground)
    }
    
    // MARK: - Spacing Tokens
    public enum Spacing {
        public static let xxSmall: CGFloat = 4
        public static let xSmall: CGFloat = 8
        public static let small: CGFloat = 12
        public static let medium: CGFloat = 16
        public static let large: CGFloat = 24
        public static let xLarge: CGFloat = 32
        public static let xxLarge: CGFloat = 48
    }
    
    // MARK: - Corner Radii
    public enum Radius {
        public static let small: CGFloat = 8
        public static let medium: CGFloat = 14
        public static let large: CGFloat = 20
        public static let pill: CGFloat = 999
    }
    
    // MARK: - Shadow Tokens
    public enum Shadow {
        public static let subtle = Color.black.opacity(0.06)
        public static let card = Color.black.opacity(0.1)
    }
}
