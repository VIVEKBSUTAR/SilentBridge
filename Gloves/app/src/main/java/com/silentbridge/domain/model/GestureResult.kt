package com.silentbridge.domain.model

data class GestureResult(
    val gestureName: String,
    val confidence: Float,
    val topPredictions: List<Pair<String, Float>> = emptyList(),
    val frames: List<SensorFrame> = emptyList(),
    val adjustedConfidence: Float = confidence,
    val feedbackGiven: Boolean = false,
    val wasCorrect: Boolean? = null
)
