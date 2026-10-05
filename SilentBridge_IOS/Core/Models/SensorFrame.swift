import Foundation

/// Data structure representing a single high-frequency sensor reading frame from the SilentBridge ESP32 glove.
public struct SensorFrame: Codable, Sendable, Identifiable, Equatable {
    public var id: UUID = UUID()
    public var timestamp: Int64
    
    // Hall sensor values (12-bit ADC, range 0..4095)
    public var thumb: Int
    public var index: Int
    public var middle: Int
    public var ring: Int
    public var little: Int
    
    // Accelerometer (m/s^2 or g-force raw float)
    public var ax: Float
    public var ay: Float
    public var az: Float
    
    // Gyroscope (deg/s or rad/s float)
    public var gx: Float
    public var gy: Float
    public var gz: Float
    
    // Euler Orientation (degrees)
    public var pitch: Float
    public var roll: Float
    
    public init(
        timestamp: Int64 = Int64(Date().timeIntervalSince1970 * 1000),
        thumb: Int = 0,
        index: Int = 0,
        middle: Int = 0,
        ring: Int = 0,
        little: Int = 0,
        ax: Float = 0,
        ay: Float = 0,
        az: Float = 0,
        gx: Float = 0,
        gy: Float = 0,
        gz: Float = 0,
        pitch: Float = 0,
        roll: Float = 0
    ) {
        self.timestamp = timestamp
        self.thumb = thumb
        self.index = index
        self.middle = middle
        self.ring = ring
        self.little = little
        self.ax = ax
        self.ay = ay
        self.az = az
        self.gx = gx
        self.gy = gy
        self.gz = gz
        self.pitch = pitch
        self.roll = roll
    }
    
    enum CodingKeys: String, CodingKey {
        case timestamp, thumb, index, middle, ring, little
        case ax, ay, az, gx, gy, gz, pitch, roll
    }
}
