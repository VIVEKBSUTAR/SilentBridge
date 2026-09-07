package com.silentbridge.domain.usecase

import com.silentbridge.domain.repository.BluetoothRepository

class DisconnectDeviceUseCase(private val repository: BluetoothRepository) {
    operator fun invoke() {
        repository.disconnect()
    }
}
