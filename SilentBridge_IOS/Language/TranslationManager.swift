import Foundation
import Translation

/// On-device offline-first translation manager for SilentBridge.
///
/// Uses Apple's native Translation framework (iOS 18+) for on-device translation.
/// `TranslationSession` is obtained via the `.translationTask()` SwiftUI modifier
/// when used in UI context, but here we use the direct session API for programmatic
/// translation from within the AppEnvironment.
///
/// This mirrors the Android ML Kit Translation pattern:
/// - Same on-device model download on first use per language pair
/// - Same graceful fallback to original text on failure
/// - Same supported language set
@MainActor
public final class TranslationManager {

    // MARK: - Session Cache

    private var sessions: [String: TranslationSession] = [:]

    public init() {}

    // MARK: - Public API

    /// Translates `text` into `targetLanguage` using Apple's on-device Translation framework.
    /// Returns the original text if translation is unavailable or fails.
    public func translate(text: String, targetLanguage: SupportedLanguage) async -> String {
        let trimmed = text.trimmingCharacters(in: .whitespacesAndNewlines)
        guard targetLanguage != .english, !trimmed.isEmpty else {
            return text
        }

        guard let targetLocale = targetLanguage.translationLocale else {
            return text
        }

        let cacheKey = targetLanguage.bcp47Tag

        let session: TranslationSession
        if let cached = sessions[cacheKey] {
            session = cached
        } else {
            // Use installedSource to avoid triggering model downloads on the fly.
            // Falls back to network-based source detection if not installed.
            let source = Locale.Language(identifier: "en")
            let newSession = TranslationSession(installedSource: source, target: targetLocale)
            sessions[cacheKey] = newSession
            session = newSession
        }

        do {
            // Ensure model is downloaded before translating
            try await session.prepareTranslation()
            let response = try await session.translate(trimmed)
            return response.targetText
        } catch {
            // Translation model not available or network error — return original
            return text
        }
    }

    // MARK: - Cache Invalidation

    public func resetSessions() {
        sessions.removeAll()
    }
}
