package com.silentbridge.data.repository

import android.content.Context
import com.google.gson.Gson
import com.google.gson.reflect.TypeToken

/**
 * Stores per-gesture feedback history using SharedPreferences.
 * Computes a running penalty multiplier based on recent wrong predictions.
 */
class FeedbackRepository(context: Context) {

    private val prefs = context.getSharedPreferences("silentbridge_feedback", Context.MODE_PRIVATE)
    private val gson = Gson()

    companion object {
        private const val WINDOW_SIZE = 20
        private const val KEY_HISTORY_PREFIX = "history_"
    }

    /** Record a feedback event. isCorrect=true for Yes, false for No. */
    fun recordFeedback(gestureName: String, isCorrect: Boolean) {
        val history = getHistory(gestureName).toMutableList()
        if (history.size >= WINDOW_SIZE) {
            history.removeAt(0)
        }
        history.add(if (isCorrect) 1 else 0)
        saveHistory(gestureName, history)
    }

    /** Returns the penalty factor [0.0, 1.0] for a given gesture based on recent history. */
    fun getPenaltyFactor(gestureName: String): Float {
        val history = getHistory(gestureName)
        if (history.isEmpty()) return 0f
        
        val wrongCount = history.count { it == 0 }
        return wrongCount.toFloat() / WINDOW_SIZE
    }

    /** Returns adjusted confidence after applying penalty. */
    fun applyPenalty(gestureName: String, rawConfidence: Float): Float {
        val penaltyFactor = getPenaltyFactor(gestureName)
        return (rawConfidence * (1f - penaltyFactor)).coerceAtLeast(0f)
    }

    /** Returns per-gesture stats: Map<gestureName, Pair<correct, wrong>> */
    fun getStats(): Map<String, Pair<Int, Int>> {
        val allPrefs = prefs.all
        val stats = mutableMapOf<String, Pair<Int, Int>>()
        
        allPrefs.keys.filter { it.startsWith(KEY_HISTORY_PREFIX) }.forEach { key ->
            val gestureName = key.removePrefix(KEY_HISTORY_PREFIX)
            val history = getHistory(gestureName)
            val correct = history.count { it == 1 }
            val wrong = history.count { it == 0 }
            stats[gestureName] = Pair(correct, wrong)
        }
        
        return stats
    }

    private fun getHistory(gestureName: String): List<Int> {
        val json = prefs.getString(KEY_HISTORY_PREFIX + gestureName, null) ?: return emptyList()
        val type = object : TypeToken<List<Int>>() {}.type
        return gson.fromJson(json, type)
    }

    private fun saveHistory(gestureName: String, history: List<Int>) {
        val json = gson.toJson(history)
        prefs.edit().putString(KEY_HISTORY_PREFIX + gestureName, json).apply()
    }

    /** Clear all history (for testing). */
    fun clearHistory() {
        prefs.edit().clear().apply()
    }
}
