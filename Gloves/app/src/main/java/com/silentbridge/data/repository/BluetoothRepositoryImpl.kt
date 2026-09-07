package com.silentbridge.data.repository

import android.bluetooth.BluetoothSocket
import android.util.Log
import com.silentbridge.data.bluetooth.BluetoothConnectionManager
import com.silentbridge.data.bluetooth.BluetoothController
import com.silentbridge.data.bluetooth.BluetoothReader
import com.silentbridge.domain.model.BluetoothDeviceDomain
import com.silentbridge.domain.model.ConnectionState
import com.silentbridge.domain.model.SensorFrame
import com.silentbridge.domain.repository.BluetoothRepository
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asSharedFlow
import kotlinx.coroutines.flow.catch
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.flow.onCompletion
import kotlinx.coroutines.withContext

class BluetoothRepositoryImpl(
    private val controller: BluetoothController,
    private val connectionManager: BluetoothConnectionManager,
    private val reader: BluetoothReader
) : BluetoothRepository {

    companion object {
        private const val TAG = "BluetoothRepo"
    }

    override val connectionState: StateFlow<ConnectionState> = controller.connectionState

    private val _sensorData = MutableSharedFlow<SensorFrame>()
    override val sensorData: Flow<SensorFrame> = _sensorData.asSharedFlow()

    private var currentSocket: BluetoothSocket? = null

    override fun getPairedDevices(): List<BluetoothDeviceDomain> {
        return controller.getPairedDevices()
    }

    override suspend fun connect(address: String): Boolean = withContext(Dispatchers.IO) {
        Log.d(TAG, "Starting connection process to $address")
        controller.updateConnectionState(ConnectionState.CONNECTING)
        
        val socket = connectionManager.connectToDevice(address)
        if (socket != null && socket.isConnected) {
            Log.d(TAG, "Connection successful, starting reader")
            currentSocket = socket
            controller.updateConnectionState(ConnectionState.CONNECTED)
            startReading(socket)
            true
        } else {
            Log.e(TAG, "Connection failed or socket is null")
            controller.updateConnectionState(ConnectionState.ERROR)
            false
        }
    }

    private suspend fun startReading(socket: BluetoothSocket) {
        reader.observeSensorData(socket)
            .onCompletion {
                Log.d(TAG, "Bluetooth reader completed")
                if (connectionState.value == ConnectionState.CONNECTED) {
                    controller.updateConnectionState(ConnectionState.DISCONNECTED)
                }
            }
            .catch { e ->
                Log.e(TAG, "Error in bluetooth reader: ${e.message}")
                controller.updateConnectionState(ConnectionState.ERROR)
            }
            .collectLatest { frame ->
                _sensorData.emit(frame)
            }
    }

    override fun disconnect() {
        connectionManager.closeConnection()
        currentSocket = null
        controller.updateConnectionState(ConnectionState.DISCONNECTED)
    }

    override fun isBluetoothEnabled(): Boolean {
        return controller.isBluetoothEnabled()
    }
}
