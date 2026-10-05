import Foundation

/// Full preprocessing pipeline preparing raw SensorFrames into a [1, 100, 13] normalized matrix.
public final class GesturePreprocessor: Sendable {
    private let featureExtractor = FeatureExtractor()
    private let resampler = Resampler()
    private let featureScaler = FeatureScaler()
    
    public init() {}
    
    public func preprocess(frames: [SensorFrame]) -> [[Float]] {
        // STEP 1: Extraction (N x 13)
        var data = featureExtractor.extractAll(frames: frames)
        
        // STEP 2: Finger Hall normalization (cols 0..4 divided by 4095.0)
        for i in 0..<data.count {
            for j in 0...4 {
                data[i][j] = data[i][j] / 4095.0
            }
        }
        
        // STEP 3: Resampling to fixed 100 length
        data = resampler.resample(data: data)
        
        // STEP 4: Standard scaling for cols 5..12
        featureScaler.scale(data: &data)
        
        return data
    }
}
