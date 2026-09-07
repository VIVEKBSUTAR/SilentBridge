package com.silentbridge.listen

import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.speech.RecognitionListener
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer
import android.util.Log

/**
 * Wraps Android SpeechRecognizer.
 * Listens once (tap to start, stops automatically when speech ends).
 * Callbacks are invoked on the main thread.
 */
class ListenManager(private val context: Context) {

    private var recognizer: SpeechRecognizer? = null

    var onResult: ((String) -> Unit)? = null
    var onError: ((String) -> Unit)? = null
    var onStarted: (() -> Unit)? = null
    var onStopped: (() -> Unit)? = null

    fun isAvailable(): Boolean = SpeechRecognizer.isRecognitionAvailable(context)

    fun startListening(languageCode: String = "en-US") {
        stopListening()

        recognizer = SpeechRecognizer.createSpeechRecognizer(context)
        recognizer?.setRecognitionListener(object : RecognitionListener {

            override fun onReadyForSpeech(params: Bundle?) {
                onStarted?.invoke()
            }

            override fun onResults(results: Bundle?) {
                val matches = results?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                val text = matches?.firstOrNull()?.trim()
                onStopped?.invoke()
                if (!text.isNullOrBlank()) {
                    onResult?.invoke(text)
                } else {
                    onError?.invoke("No speech detected")
                }
            }

            override fun onError(error: Int) {
                onStopped?.invoke()
                val msg = when (error) {
                    SpeechRecognizer.ERROR_AUDIO             -> "Audio recording error"
                    SpeechRecognizer.ERROR_CLIENT            -> "Client error"
                    SpeechRecognizer.ERROR_INSUFFICIENT_PERMISSIONS -> "Microphone permission denied"
                    SpeechRecognizer.ERROR_NETWORK           -> "Network error"
                    SpeechRecognizer.ERROR_NETWORK_TIMEOUT   -> "Network timeout"
                    SpeechRecognizer.ERROR_NO_MATCH          -> "No speech recognised"
                    SpeechRecognizer.ERROR_RECOGNIZER_BUSY   -> "Recogniser busy — try again"
                    SpeechRecognizer.ERROR_SERVER            -> "Server error"
                    SpeechRecognizer.ERROR_SPEECH_TIMEOUT    -> "No speech detected"
                    else                                     -> "Unknown error ($error)"
                }
                Log.e("ListenManager", "STT error: $msg")
                onError?.invoke(msg)
            }

            override fun onBeginningOfSpeech()           {}
            override fun onBufferReceived(buffer: ByteArray?) {}
            override fun onEndOfSpeech()                 {}
            override fun onEvent(eventType: Int, params: Bundle?) {}
            override fun onPartialResults(partialResults: Bundle?) {}
            override fun onRmsChanged(rmsdB: Float)      {}
        })

        val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
            putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
            putExtra(RecognizerIntent.EXTRA_LANGUAGE, "en-US")   // always capture in English
            putExtra(RecognizerIntent.EXTRA_LANGUAGE_PREFERENCE, "en-US")
            // Use string literal to avoid unresolved reference issues in certain SDK configurations
            putExtra("android.speech.extra.ONLY_RETURN_LANGUAGE_MATCHES", true)
            putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 1)
            putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, false)
        }

        recognizer?.startListening(intent)
    }

    fun stopListening() {
        recognizer?.stopListening()
        recognizer?.destroy()
        recognizer = null
    }

    fun destroy() {
        stopListening()
    }
}
