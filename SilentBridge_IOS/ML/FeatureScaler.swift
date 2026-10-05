import Foundation

public struct ScalerParams: Codable, Sendable {
    public var mean: [Float]
    public var scale: [Float]
    public var feature_names: [String]?
}

/// Standard scaler applying z-score normalization ((val - mean) / scale) to IMU columns 5..12.
public final class FeatureScaler: @unchecked Sendable {
    private var params: ScalerParams?
    
    public init() {
        loadParams()
    }
    
    public func loadParams() {
        guard let url = Bundle.main.url(forResource: "scaler_params", withExtension: "json") else {
            return
        }
        do {
            let data = try Data(contentsOf: url)
            self.params = try JSONDecoder().decode(ScalerParams.self, from: data)
        } catch {
            // Log fallback
        }
    }
    
    /// Applies Standard Scaler normalization in-place to columns 5-12 (ax, ay, az, gx, gy, gz, pitch, roll).
    public func scale(data: inout [[Float]]) {
        guard let p = params else { return }
        
        for i in 0..<data.count {
            for j in 5...12 {
                let paramIdx = j - 5
                if paramIdx >= 0 && paramIdx < p.mean.count && paramIdx < p.scale.count {
                    data[i][j] = (data[i][j] - p.mean[paramIdx]) / p.scale[paramIdx]
                }
            }
        }
    }
}
