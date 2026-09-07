package com.silentbridge.ml

import android.util.Log
import com.silentbridge.domain.model.SensorFrame

class GesturePreprocessor(
    private val featureExtractor: FeatureExtractor,
    private val resampler: Resampler,
    private val scaler: FeatureScaler
) {
    companion object {
        private const val TAG = "GesturePreprocessor"
    }

    fun preprocess(frames: List<SensorFrame>): Array<Array<FloatArray>> {
        Log.d(TAG, "Input frames count: ${frames.size}")
        
        // STEP 1: FEATURE EXTRACTION (N x 13)
        var data = featureExtractor.extractAll(frames)
        Log.d(TAG, "Matrix shape after extraction: ${data.size}x13")
        
        // STEP 2: NORMALIZE FINGERS (0-4)
        for (row in data) {
            for (j in 0..4) {
                row[j] = row[j] / 4095.0f
            }
        }
        
        // STEP 3: RESAMPLING (100 x 13)
        data = resampler.resample(data)
        Log.d(TAG, "Matrix shape after resampling: ${data.size}x13")
        
        // STEP 4: STANDARD SCALER (5-12)
        data = scaler.scale(data)
        
        // FINAL: Wrap in batch dimension [1, 100, 13]
        return arrayOf(data)
    }
}
