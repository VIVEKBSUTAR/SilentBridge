package com.silentbridge.data.feedback

import android.content.Context
import android.content.Intent
import android.net.Uri
import androidx.core.content.FileProvider
import android.util.Log

class FeedbackExporter(private val context: Context, private val logger: FeedbackLogger) {

    companion object {
        private const val TAG = "FeedbackExporter"
        private const val AUTHORITY = "com.example.gloves2.fileprovider"
    }

    fun exportDataset() {
        val file = logger.getLogFile()
        if (!file.exists()) {
            Log.e(TAG, "Log file does not exist")
            return
        }

        try {
            val contentUri: Uri = FileProvider.getUriForFile(context, AUTHORITY, file)
            val intent = Intent(Intent.ACTION_SEND).apply {
                type = "application/json"
                putExtra(Intent.EXTRA_STREAM, contentUri)
                addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
                putExtra(Intent.EXTRA_SUBJECT, "SilentBridge Gesture Dataset")
                putExtra(Intent.EXTRA_TEXT, "Feedback log exported from SilentBridge app.")
            }
            
            val chooser = Intent.createChooser(intent, "Share Dataset")
            chooser.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            context.startActivity(chooser)
        } catch (e: Exception) {
            Log.e(TAG, "Error exporting dataset: ${e.message}", e)
        }
    }
}
