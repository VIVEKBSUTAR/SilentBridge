package com.silentbridge.data.feedback

import android.content.Context
import android.os.Build
import android.util.Log
import com.silentbridge.domain.model.GestureResult
import com.silentbridge.domain.model.SensorFrame
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import java.io.File
import java.text.SimpleDateFormat
import java.util.*

class FeedbackLogger(private val context: Context) {

    companion object {
        private const val TAG = "FeedbackLogger"
        private const val FILENAME = "feedback_log.jsonl"
        private const val MODEL_VERSION = "silentbridge_v1"
    }

    private val json = Json {
        encodeDefaults = true
        ignoreUnknownKeys = true
    }

    private val dateFormat = SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss", Locale.getDefault())

    suspend fun saveFeedback(
        result: GestureResult,
        confirmed: Boolean,
        correctLabel: String?
    ) = withContext(Dispatchers.IO) {
        try {
            val entry = FeedbackEntry(
                time = dateFormat.format(Date()),
                predicted = result.gestureName,
                confidence = result.confidence,
                confirmed = confirmed,
                correct_label = correctLabel ?: result.gestureName,
                frame_count = result.frames.size,
                model = MODEL_VERSION,
                frames = result.frames,
                deviceInfo = "${Build.MANUFACTURER} ${Build.MODEL} (Android ${Build.VERSION.RELEASE})"
            )

            val line = json.encodeToString(entry) + "\n"
            val file = getLogFile()
            file.appendText(line)
            
            Log.d(TAG, "Feedback saved. Total frames: ${entry.frame_count}. Prediction: ${entry.predicted}. Correct: ${entry.correct_label}")
            Log.d(TAG, "Log file path: ${file.absolutePath}")
        } catch (e: Exception) {
            Log.e(TAG, "Error saving feedback: ${e.message}", e)
        }
    }

    fun getLogFile(): File {
        val dir = context.getExternalFilesDir(null)
        return File(dir, FILENAME)
    }

    fun getFeedbackCount(): Int {
        val file = getLogFile()
        if (!file.exists()) return 0
        return file.readLines().size
    }

    fun clearFeedback() {
        val file = getLogFile()
        if (file.exists()) {
            file.delete()
        }
    }
}
