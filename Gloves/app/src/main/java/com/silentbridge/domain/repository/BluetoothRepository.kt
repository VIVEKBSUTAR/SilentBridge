package com.silentbridge.domain.repository

import com.silentbridge.domain.model.BluetoothDeviceDomain
import com.silentbridge.domain.model.ConnectionState
import com.silentbridge.domain.model.SensorFrame
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.StateFlow

interface BluetoothRepository {
    val connectionState: StateFlow<ConnectionState>
    val sensorData: Flow<SensorFrame>
    
    fun getPairedDevices(): List<BluetoothDeviceDomain>
    suspend fun connect(address: String): Boolean
    fun disconnect()
    fun isBluetoothEnabled(): Boolean
}
