package com.silentbridge.domain.model

import kotlinx.serialization.Serializable

@Serializable
data class SensorFrame(
    val timestamp: Long = 0L,
    // Finger sensors
    val thumb: Int = 0,
    val index: Int = 0,
    val middle: Int = 0,
    val ring: Int = 0,
    val little: Int = 0,
    // Accelerometer
    val ax: Float = 0f,
    val ay: Float = 0f,
    val az: Float = 0f,
    // Gyroscope
    val gx: Float = 0f,
    val gy: Float = 0f,
    val gz: Float = 0f,
    // Orientation
    val pitch: Float = 0f,
    val roll: Float = 0f
)
