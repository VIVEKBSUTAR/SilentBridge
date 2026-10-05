import Foundation

/// Sealed enum for supported translation and speech output languages.
public enum SupportedLanguage: String, Codable, Sendable, CaseIterable, Identifiable {
    case english = "en"
    case hindi = "hi"
    case marathi = "mr"
    case gujarati = "gu"
    case tamil = "ta"
    case telugu = "te"
    case kannada = "kn"
    case malayalam = "ml"
    
    public var id: String { rawValue }
    
    public var code: String { rawValue }
    
    public var displayName: String {
        switch self {
        case .english: return "English"
        case .hindi: return "Hindi"
        case .marathi: return "Marathi"
        case .gujarati: return "Gujarati"
        case .tamil: return "Tamil"
        case .telugu: return "Telugu"
        case .kannada: return "Kannada"
        case .malayalam: return "Malayalam"
        }
    }
    
    public var nativeName: String {
        switch self {
        case .english: return "English"
        case .hindi: return "हिंदी"
        case .marathi: return "मराठी"
        case .gujarati: return "ગુજરાતી"
        case .tamil: return "தமிழ்"
        case .telugu: return "తెలుగు"
        case .kannada: return "ಕನ್ನಡ"
        case .malayalam: return "മലയാളം"
        }
    }
    
    public var bcp47Tag: String {
        switch self {
        case .english: return "en-US"
        case .hindi: return "hi-IN"
        case .marathi: return "mr-IN"
        case .gujarati: return "gu-IN"
        case .tamil: return "ta-IN"
        case .telugu: return "te-IN"
        case .kannada: return "kn-IN"
        case .malayalam: return "ml-IN"
        }
    }
    
    public static func fromCode(_ code: String) -> SupportedLanguage {
        SupportedLanguage(rawValue: code.lowercased()) ?? .english
    }

    /// Returns the `Locale.Language` identifier used by Apple's Translation framework.
    /// Returns `nil` for English (no translation needed) or unsupported pairs.
    public var translationLocale: Locale.Language? {
        switch self {
        case .english:   return nil          // source language — no translation
        case .hindi:     return Locale.Language(identifier: "hi")
        case .marathi:   return Locale.Language(identifier: "mr")
        case .gujarati:  return Locale.Language(identifier: "gu")
        case .tamil:     return Locale.Language(identifier: "ta")
        case .telugu:    return Locale.Language(identifier: "te")
        case .kannada:   return Locale.Language(identifier: "kn")
        case .malayalam: return Locale.Language(identifier: "ml")
        }
    }
}
