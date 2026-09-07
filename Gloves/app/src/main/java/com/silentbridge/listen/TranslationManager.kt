package com.silentbridge.listen

import android.util.Log
import com.google.mlkit.common.model.DownloadConditions
import com.google.mlkit.nl.translate.TranslateLanguage
import com.google.mlkit.nl.translate.Translation
import com.google.mlkit.nl.translate.TranslatorOptions

/**
 * Wraps ML Kit on-device translation.
 * Source is always English. Target is whatever the user picks.
 * Models are downloaded once on first use (~30MB per language).
 */
class TranslationManager {

    // Supported languages for the disabled user to choose from
    companion object {
        val SUPPORTED_LANGUAGES = listOf(
            "en"    to "English",
            "hi"    to "Hindi",
            "mr"    to "Marathi",
            "ta"    to "Tamil",
            "te"    to "Telugu",
            "bn"    to "Bengali",
            "kn"    to "Kannada",
            "gu"    to "Gujarati",
            "pa"    to "Punjabi",
            "es"    to "Spanish",
            "fr"    to "French",
            "ar"    to "Arabic",
            "zh"    to "Chinese",
            "ja"    to "Japanese",
            "de"    to "German",
        )

        fun getLabel(code: String): String =
            SUPPORTED_LANGUAGES.firstOrNull { it.first == code }?.second ?: code
    }

    fun translate(
        text: String,
        targetLanguageCode: String,
        onSuccess: (String) -> Unit,
        onFailure: (String) -> Unit
    ) {
        // If target is English, no translation needed
        if (targetLanguageCode == "en") {
            onSuccess(text)
            return
        }

        val mlKitCode = TranslateLanguage.fromLanguageTag(targetLanguageCode)
        if (mlKitCode == null) {
            onFailure("Unsupported language: $targetLanguageCode")
            return
        }

        val options = TranslatorOptions.Builder()
            .setSourceLanguage(TranslateLanguage.ENGLISH)
            .setTargetLanguage(mlKitCode)
            .build()

        val translator = Translation.getClient(options)
        val conditions = DownloadConditions.Builder().build()  // allow download on any network

        translator.downloadModelIfNeeded(conditions)
            .addOnSuccessListener {
                translator.translate(text)
                    .addOnSuccessListener { translated ->
                        translator.close()
                        onSuccess(translated)
                    }
                    .addOnFailureListener { e ->
                        translator.close()
                        Log.e("TranslationManager", "Translation failed: ${e.message}")
                        onFailure("Translation failed: ${e.message}")
                    }
            }
            .addOnFailureListener { e ->
                translator.close()
                Log.e("TranslationManager", "Model download failed: ${e.message}")
                onFailure("Language model download failed. Check internet connection.")
            }
    }
}
