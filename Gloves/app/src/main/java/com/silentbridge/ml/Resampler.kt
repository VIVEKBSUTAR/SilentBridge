package com.silentbridge.ml

class Resampler {
    companion object {
        private const val TARGET_LENGTH = 100
    }

    fun resample(data: Array<FloatArray>): Array<FloatArray> {
        val n = data.size
        if (n == 0) return Array(TARGET_LENGTH) { FloatArray(0) }
        
        val numFeatures = data[0].size
        val resampled = Array(TARGET_LENGTH) { FloatArray(numFeatures) }

        for (i in 0 until TARGET_LENGTH) {
            val relativePos = i.toFloat() / (TARGET_LENGTH - 1) * (n - 1)
            val index = relativePos.toInt()
            val fraction = relativePos - index

            if (index >= n - 1) {
                resampled[i] = data[n - 1].copyOf()
            } else {
                for (j in 0 until numFeatures) {
                    resampled[i][j] = data[index][j] * (1 - fraction) + data[index + 1][j] * fraction
                }
            }
        }
        return resampled
    }
}
