package com.silentbridge.ml

import android.content.Context
import android.util.Log
import org.json.JSONObject

class LabelMapper(private val context: Context) {
    private var labels = mutableMapOf<Int, String>()

    fun load() {
        try {
            val jsonString = context.assets.open("label_map.json")
                .bufferedReader().use { it.readText() }
            val jsonObj = JSONObject(jsonString)
            val reverseMap = mutableMapOf<Int, String>()
            jsonObj.keys().forEach { key ->
                reverseMap[jsonObj.getInt(key)] = key
            }
            labels = reverseMap
            Log.i("LabelMapper", "Loaded ${labels.size} labels: $labels")
        } catch (e: Exception) {
            Log.e("LabelMapper", "Error loading label_map.json: ${e.message}")
            // Fallback
            labels = mutableMapOf(
                0 to "ALL", 1 to "FOOD", 2 to "HELLO", 3 to "HELP", 4 to "I",
                5 to "MEDICINE", 6 to "NEED", 7 to "NO", 8 to "THANK_YOU",
                9 to "WANT", 10 to "WATER", 11 to "YES", 12 to "YOU"
            )
        }
    }

    fun getLabel(index: Int): String {
        return labels[index] ?: "UNKNOWN"
    }
}
