package com.silentbridge.presentation.viewmodel

import android.app.Application
import android.content.Context
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import com.silentbridge.data.bluetooth.BluetoothConnectionManager
import com.silentbridge.data.bluetooth.BluetoothController
import com.silentbridge.data.bluetooth.BluetoothReader
import com.silentbridge.data.bluetooth.SensorPacketParser
import com.silentbridge.data.feedback.FeedbackExporter
import com.silentbridge.data.feedback.FeedbackLogger
import com.silentbridge.data.repository.BluetoothRepositoryImpl
import com.silentbridge.data.repository.FeedbackRepository
import com.silentbridge.domain.usecase.*
import com.silentbridge.gesture.GestureEngine
import com.silentbridge.gesture.GestureRecorder
import com.silentbridge.gesture.MotionDetector
import com.silentbridge.ml.*

class ViewModelFactory(private val context: Context) : ViewModelProvider.Factory {
    override fun <T : ViewModel> create(modelClass: Class<T>): T {
        if (modelClass.isAssignableFrom(MainViewModel::class.java)) {
            val controller = BluetoothController(context)
            val connectionManager = BluetoothConnectionManager(context)
            val parser = SensorPacketParser()
            val reader = BluetoothReader(parser)
            val repository = BluetoothRepositoryImpl(controller, connectionManager, reader)
            val feedbackRepository = FeedbackRepository(context)
            val feedbackLogger = FeedbackLogger(context)
            val feedbackExporter = FeedbackExporter(context, feedbackLogger)
            
            // Phase 2 components
            val motionDetector = MotionDetector()
            val recorder = GestureRecorder()
            val featureExtractor = FeatureExtractor()
            val resampler = Resampler()
            val scaler = FeatureScaler(context).apply { load() }
            val preprocessor = GesturePreprocessor(featureExtractor, resampler, scaler)
            val classifier = GestureClassifier(context).apply { load() }
            val labelMapper = LabelMapper(context).apply { load() }
            
            val gestureEngine = GestureEngine(
                motionDetector,
                recorder,
                preprocessor,
                classifier,
                labelMapper
            )
            
            @Suppress("UNCHECKED_CAST")
            return MainViewModel(
                context.applicationContext as Application,
                GetPairedDevicesUseCase(repository),
                ConnectDeviceUseCase(repository),
                DisconnectDeviceUseCase(repository),
                ObserveSensorDataUseCase(repository),
                ObserveConnectionStateUseCase(repository),
                gestureEngine,
                feedbackRepository,
                feedbackLogger,
                feedbackExporter
            ) as T
        }
        throw IllegalArgumentException("Unknown ViewModel class")
    }
}
