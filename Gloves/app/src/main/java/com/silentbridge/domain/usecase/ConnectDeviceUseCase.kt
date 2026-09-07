package com.silentbridge.domain.usecase

import com.silentbridge.domain.repository.BluetoothRepository

class ConnectDeviceUseCase(private val repository: BluetoothRepository) {
    suspend operator fun invoke(address: String): Boolean {
        return repository.connect(address)
    }
}
