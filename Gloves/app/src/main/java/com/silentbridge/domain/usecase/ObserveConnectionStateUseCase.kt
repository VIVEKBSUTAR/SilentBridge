package com.silentbridge.domain.usecase

import com.silentbridge.domain.model.ConnectionState
import com.silentbridge.domain.repository.BluetoothRepository
import kotlinx.coroutines.flow.StateFlow

class ObserveConnectionStateUseCase(private val repository: BluetoothRepository) {
    operator fun invoke(): StateFlow<ConnectionState> {
        return repository.connectionState
    }
}
