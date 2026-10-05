import Foundation

/// State of the Bluetooth connection to the SilentBridge ESP32 glove.
public enum ConnectionState: String, Codable, Sendable, CustomStringConvertible {
    case disconnected = "Disconnected"
    case connecting = "Connecting..."
    case connected = "Connected"
    case disconnecting = "Disconnecting..."
    case error = "Error"
    
    public var description: String { rawValue }
    
    public var isConnected: BooleanLiteralType {
        self == .connected
    }
}
