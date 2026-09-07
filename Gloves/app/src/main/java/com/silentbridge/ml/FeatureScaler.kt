package com.silentbridge.ml

import android.content.Context
import android.util.Log
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json

@Serializable
data class ScalerParams(
    val mean: List<Float>,
    val scale: List<Float>
)

class FeatureScaler(private val context: Context) {
    private var params: ScalerParams? = null
    private val json = Json { ignoreUnknownKeys = true }

    fun load() {
        try {
            val jsonString = context.assets.open("scaler_params.json").bufferedReader().use { it.readText() }
            params = json.decodeFromString<ScalerParams>(jsonString)
            Log.i("FeatureScaler", "Loaded scaler: scaler_params.json (Mean size: ${params?.mean?.size}, Scale size: ${params?.scale?.size})")
        } catch (e: Exception) {
            Log.e("FeatureScaler", "Error loading scaler_params.json: ${e.message}")
        }
    }

    fun scale(data: Array<FloatArray>): Array<FloatArray> {
        val p = params ?: return data
        
        for (row in data) {
            // Apply Standard Scaler to columns 5-12 (ax, ay, az, gx, gy, gz, pitch, roll)
            for (j in 5..12) {
                val paramIdx = j - 5
                if (paramIdx >= 0 && paramIdx < p.mean.size && paramIdx < p.scale.size) {
                    row[j] = (row[j] - p.mean[paramIdx]) / p.scale[paramIdx]
                }
            }
        }
        return data
    }
}
