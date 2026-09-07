package com.silentbridge.domain.usecase

import com.silentbridge.domain.model.BluetoothDeviceDomain
import com.silentbridge.domain.repository.BluetoothRepository

class GetPairedDevicesUseCase(private val repository: BluetoothRepository) {
    operator fun invoke(): List<BluetoothDeviceDomain> {
        return repository.getPairedDevices()
    }
}
