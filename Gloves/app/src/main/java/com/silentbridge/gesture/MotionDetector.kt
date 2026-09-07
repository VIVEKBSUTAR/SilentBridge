package com.silentbridge.gesture

import com.silentbridge.domain.model.SensorFrame
import kotlin.math.sqrt

class MotionDetector {
    fun calculateMagnitude(frame: SensorFrame): Double {
        return sqrt(
            (frame.gx * frame.gx + frame.gy * frame.gy + frame.gz * frame.gz).toDouble()
        )
    }

    fun isMoving(magnitude: Double, threshold: Double): Boolean {
        return magnitude > threshold
    }
}
