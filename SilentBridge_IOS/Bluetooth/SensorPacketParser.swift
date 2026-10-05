import Foundation

/// Parses raw JSON sensor line strings emitted by the ESP32 glove into strongly-typed `SensorFrame` objects.
public final class SensorPacketParser: Sendable {
    private let decoder: JSONDecoder
    
    public init() {
        let decoder = JSONDecoder()
        decoder.keyDecodingStrategy = .useDefaultKeys
        self.decoder = decoder
    }
    
    public func parse(jsonString: String) -> SensorFrame? {
        guard let data = jsonString.data(using: .utf8) else { return nil }
        do {
            return try decoder.decode(SensorFrame.self, from: data)
        } catch {
            return nil
        }
    }
}
