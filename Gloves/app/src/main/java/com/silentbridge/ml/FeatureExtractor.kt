package com.silentbridge.ml

import com.silentbridge.domain.model.SensorFrame

class FeatureExtractor {
    fun extract(frame: SensorFrame): FloatArray {
        return floatArrayOf(
            frame.thumb.toFloat(),
            frame.index.toFloat(),
            frame.middle.toFloat(),
            frame.ring.toFloat(),
            frame.little.toFloat(),
            frame.ax,
            frame.ay,
            frame.az,
            frame.gx,
            frame.gy,
            frame.gz,
            frame.pitch,
            frame.roll
        )
    }

    fun extractAll(frames: List<SensorFrame>): Array<FloatArray> {
        return frames.map { extract(it) }.toTypedArray()
    }
}
