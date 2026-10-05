import Foundation

public enum GestureIntent: String, Codable, Sendable {
    case emergency = "Emergency"
    case request = "Request"
    case question = "Question"
    case confirmation = "Confirmation"
    case negation = "Negation"
    case greeting = "Greeting"
    case closing = "Closing"
    case unknown = "Unknown"
}
