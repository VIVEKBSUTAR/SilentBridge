import Foundation

/// Representation of a Bluetooth device (discovered or connected).
public struct BluetoothDevice: Identifiable, Codable, Sendable, Equatable, Hashable {
    public var id: String { address }
    public var name: String
    public var address: String
    public var rssi: Int
    public var isConnected: Bool
    
    public init(name: String, address: String, rssi: Int = -60, isConnected: Bool = false) {
        self.name = name.isEmpty ? "Unknown Glove" : name
        self.address = address
        self.rssi = rssi
        self.isConnected = isConnected
    }
}
