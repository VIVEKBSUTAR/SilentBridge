import SwiftUI

// MARK: - Premium Glass Card Component
public struct SBGlassCard<Content: View>: View {
    private let content: Content
    private let padding: CGFloat
    private let cornerRadius: CGFloat
    
    public init(
        padding: CGFloat = SBTheme.Spacing.medium,
        cornerRadius: CGFloat = SBTheme.Radius.large,
        @ViewBuilder content: () -> Content
    ) {
        self.padding = padding
        self.cornerRadius = cornerRadius
        self.content = content()
    }
    
    public var body: some View {
        VStack(alignment: .leading, spacing: SBTheme.Spacing.small) {
            content
        }
        .padding(padding)
        .background(
            RoundedRectangle(cornerRadius: cornerRadius, style: .continuous)
                .fill(SBTheme.Colors.glassFill)
                .shadow(color: SBTheme.Shadow.subtle, radius: 8, x: 0, y: 3)
        )
        .overlay(
            RoundedRectangle(cornerRadius: cornerRadius, style: .continuous)
                .stroke(SBTheme.Colors.cardBorder, lineWidth: 1)
        )
    }
}

// MARK: - Status Badge Component
public struct SBStatusBadge: View {
    let title: String
    let icon: String
    let color: Color
    
    public init(title: String, icon: String, color: Color) {
        self.title = title
        self.icon = icon
        self.color = color
    }
    
    public var body: some View {
        HStack(spacing: 6) {
            Circle()
                .fill(color)
                .frame(width: 8, height: 8)
            
            Image(systemName: icon)
                .font(.caption2.weight(.semibold))
                .foregroundColor(color)
            
            Text(title)
                .font(.caption.weight(.semibold))
                .foregroundColor(.primary)
        }
        .padding(.horizontal, 10)
        .padding(.vertical, 5)
        .background(color.opacity(0.12))
        .clipShape(Capsule())
    }
}

// MARK: - Primary Action Button
public struct SBPrimaryButton: View {
    let title: String
    let icon: String?
    let isLoading: Bool
    let color: Color
    let action: () -> Void
    
    public init(
        title: String,
        icon: String? = nil,
        isLoading: Bool = false,
        color: Color = SBTheme.Colors.primary,
        action: @escaping () -> Void
    ) {
        self.title = title
        self.icon = icon
        self.isLoading = isLoading
        self.color = color
        self.action = action
    }
    
    public var body: some View {
        Button(action: action) {
            HStack(spacing: SBTheme.Spacing.small) {
                if isLoading {
                    ProgressView()
                        .tint(.white)
                } else if let icon = icon {
                    Image(systemName: icon)
                        .font(.headline)
                }
                
                Text(title)
                    .font(.headline.weight(.bold))
            }
            .frame(maxWidth: .infinity)
            .padding(.vertical, 14)
            .background(color)
            .foregroundColor(.white)
            .clipShape(RoundedRectangle(cornerRadius: SBTheme.Radius.medium, style: .continuous))
            .shadow(color: color.opacity(0.3), radius: 6, x: 0, y: 3)
        }
        .disabled(isLoading)
    }
}

// MARK: - Secondary Action Button
public struct SBSecondaryButton: View {
    let title: String
    let icon: String?
    let action: () -> Void
    
    public init(title: String, icon: String? = nil, action: @escaping () -> Void) {
        self.title = title
        self.icon = icon
        self.action = action
    }
    
    public var body: some View {
        Button(action: action) {
            HStack(spacing: SBTheme.Spacing.xSmall) {
                if let icon = icon {
                    Image(systemName: icon)
                        .font(.subheadline.weight(.semibold))
                }
                Text(title)
                    .font(.subheadline.weight(.semibold))
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 10)
            .background(SBTheme.Colors.secondaryBackground)
            .foregroundColor(.primary)
            .clipShape(RoundedRectangle(cornerRadius: SBTheme.Radius.medium, style: .continuous))
        }
    }
}

// MARK: - Gesture Word Pill
public struct SBGesturePill: View {
    let word: String
    let onRemove: (() -> Void)?
    
    public init(word: String, onRemove: (() -> Void)? = nil) {
        self.word = word
        self.onRemove = onRemove
    }
    
    public var body: some View {
        HStack(spacing: 6) {
            Text(word)
                .font(.subheadline.weight(.bold))
                .foregroundColor(.primary)
            
            if let onRemove = onRemove {
                Button(action: onRemove) {
                    Image(systemName: "xmark.circle.fill")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 7)
        .background(SBTheme.Colors.primary.opacity(0.12))
        .overlay(
            Capsule()
                .stroke(SBTheme.Colors.primary.opacity(0.25), lineWidth: 1)
        )
        .clipShape(Capsule())
    }
}
