import Foundation

/// Linear interpolation resampler mapping variable length sensor streams to fixed 100 sequence frames.
public struct Resampler: Sendable {
    public static let targetLength: Int = 100
    
    public init() {}
    
    public func resample(data: [[Float]]) -> [[Float]] {
        let n = data.count
        guard n > 0 else { return Array(repeating: Array(repeating: 0.0, count: 13), count: Self.targetLength) }
        
        let numFeatures = data[0].count
        var resampled = Array(repeating: Array(repeating: Float(0.0), count: numFeatures), count: Self.targetLength)
        
        for i in 0..<Self.targetLength {
            let relativePos = Float(i) / Float(Self.targetLength - 1) * Float(n - 1)
            let index = Int(relativePos)
            let fraction = relativePos - Float(index)
            
            if index >= n - 1 {
                resampled[i] = data[n - 1]
            } else {
                for j in 0..<numFeatures {
                    resampled[i][j] = data[index][j] * (1.0 - fraction) + data[index + 1][j] * fraction
                }
            }
        }
        
        return resampled
    }
}
