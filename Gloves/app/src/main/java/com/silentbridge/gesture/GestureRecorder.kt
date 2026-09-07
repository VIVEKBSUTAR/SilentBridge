package com.silentbridge.gesture

import com.silentbridge.domain.model.SensorFrame

class GestureRecorder {
    private val recordedFrames = mutableListOf<SensorFrame>()
    private var idleCounter = 0

    companion object {
        const val IDLE_SETTLE_FRAMES = 15
        const val MIN_GESTURE_FRAMES = 15
    }

    fun start() {
        recordedFrames.clear()
        idleCounter = 0
    }

    fun addFrame(frame: SensorFrame) {
        recordedFrames.add(frame)
    }

    /**
     * Updates idle counter and returns true if gesture should end.
     */
    fun updateIdleState(isQuiet: Boolean): Boolean {
        if (isQuiet) {
            idleCounter++
        } else {
            idleCounter = 0
        }
        return idleCounter >= IDLE_SETTLE_FRAMES
    }

    fun getValidGesture(): List<SensorFrame>? {
        val gestureFrames = if (recordedFrames.size > IDLE_SETTLE_FRAMES) {
            recordedFrames.dropLast(IDLE_SETTLE_FRAMES)
        } else {
            emptyList()
        }

        return if (gestureFrames.size >= MIN_GESTURE_FRAMES) {
            gestureFrames
        } else {
            null
        }
    }

    fun clear() {
        recordedFrames.clear()
        idleCounter = 0
    }
}
