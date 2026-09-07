package com.silentbridge.data.feedback

import com.silentbridge.domain.model.SensorFrame
import kotlinx.serialization.Serializable

@Serializable
data class FeedbackEntry(
    val time: String,
    val predicted: String,
    val confidence: Float,
    val confirmed: Boolean,
    val correct_label: String?,
    val frame_count: Int,
    val model: String,
    val frames: List<SensorFrame>,
    val deviceInfo: String? = null
)
