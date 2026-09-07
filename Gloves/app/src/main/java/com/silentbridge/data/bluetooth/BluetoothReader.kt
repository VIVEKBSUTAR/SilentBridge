package com.silentbridge.data.bluetooth

import android.bluetooth.BluetoothSocket
import com.silentbridge.domain.model.SensorFrame
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.flow.flowOn
import java.io.BufferedReader
import java.io.InputStreamReader

class BluetoothReader(private val parser: SensorPacketParser) {

    fun observeSensorData(socket: BluetoothSocket): Flow<SensorFrame> = flow {
        val reader = BufferedReader(InputStreamReader(socket.inputStream))
        try {
            while (socket.isConnected) {
                val line = reader.readLine() ?: break
                if (line.isBlank()) continue
                
                val frame = parser.parse(line)
                if (frame != null) {
                    emit(frame)
                }
            }
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }.flowOn(Dispatchers.IO)
}
