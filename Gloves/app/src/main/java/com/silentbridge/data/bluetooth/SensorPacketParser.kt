package com.silentbridge.data.bluetooth

import com.silentbridge.domain.model.SensorFrame
import kotlinx.serialization.json.Json

class SensorPacketParser {
    private val json = Json {
        ignoreUnknownKeys = true
        coerceInputValues = true
    }

    fun parse(jsonString: String): SensorFrame? {
        return try {
            json.decodeFromString<SensorFrame>(jsonString)
        } catch (e: Exception) {
            e.printStackTrace()
            null
        }
    }
}
