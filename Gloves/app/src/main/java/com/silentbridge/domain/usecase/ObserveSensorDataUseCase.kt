package com.silentbridge.domain.usecase

import com.silentbridge.domain.model.SensorFrame
import com.silentbridge.domain.repository.BluetoothRepository
import kotlinx.coroutines.flow.Flow

class ObserveSensorDataUseCase(private val repository: BluetoothRepository) {
    operator fun invoke(): Flow<SensorFrame> {
        return repository.sensorData
    }
}
