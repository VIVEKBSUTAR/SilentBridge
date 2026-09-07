package com.silentbridge.ml

import android.content.Context
import android.util.Log
import org.tensorflow.lite.Interpreter
import org.tensorflow.lite.flex.FlexDelegate
import java.io.FileInputStream
import java.nio.MappedByteBuffer
import java.nio.channels.FileChannel

class GestureClassifier(private val context: Context) {
    private var interpreter: Interpreter? = null
    private var outputSize: Int = 0

    companion object {
        private const val TAG = "GestureClassifier"
        private const val MODEL_PATH = "silentbridge_standard (3).tflite"
    }

    fun load() {
        try {
            val options = Interpreter.Options()
            // IMPORTANT: BiLSTM with Select TF Ops requires FlexDelegate
            options.addDelegate(FlexDelegate())
            
            val model = loadModelFile()
            val interp = Interpreter(model, options)
            interpreter = interp

            val outputShape = interp.getOutputTensor(0).shape()
            outputSize = outputShape[1]
            
            Log.i(TAG, "Loaded model: $MODEL_PATH")
            Log.i(TAG, "Output tensor shape: ${outputShape.contentToString()}")
            Log.i(TAG, "Input Shape: ${interp.getInputTensor(0).shape().contentToString()}")
            Log.i(TAG, "Detected output classes: $outputSize")
            
            Log.d(TAG, "TFLite model loaded successfully with FlexDelegate")
        } catch (e: Exception) {
            Log.e(TAG, "Error loading TFLite model: ${e.message}")
        }
    }

    private fun loadModelFile(): MappedByteBuffer {
        val fileDescriptor = context.assets.openFd(MODEL_PATH)
        val inputStream = FileInputStream(fileDescriptor.fileDescriptor)
        val fileChannel = inputStream.channel
        return fileChannel.map(
            FileChannel.MapMode.READ_ONLY,
            fileDescriptor.startOffset,
            fileDescriptor.declaredLength
        )
    }

    /**
     * Input shape: [1][100][13]
     * Output shape: dynamic [1][N]
     */
    fun classify(input: Array<Array<FloatArray>>): FloatArray {
        if (interpreter == null || outputSize == 0) {
            Log.e(TAG, "Interpreter not initialized or output size unknown")
            return floatArrayOf()
        }

        val output = Array(1) { FloatArray(outputSize) }
        try {
            val numFrames = input[0].size
            val numFeatures = input[0][0].size
            Log.i(TAG, "Captured frame count: $numFrames")
            Log.i(TAG, "Tensor shape: [1][$numFrames][$numFeatures]")
            
            val startTime = System.currentTimeMillis()
            interpreter?.run(input, output)
            val inferenceTime = System.currentTimeMillis() - startTime
            Log.i(TAG, "Inference time: ${inferenceTime}ms")
            
            Log.i(TAG, "Inference completed.")
        } catch (e: Exception) {
            Log.e(TAG, "Error during inference: ${e.message}")
        }
        return output[0]
    }

    fun close() {
        interpreter?.close()
        interpreter = null
    }
}
