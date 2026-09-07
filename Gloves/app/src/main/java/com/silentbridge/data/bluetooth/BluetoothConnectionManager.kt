package com.silentbridge.data.bluetooth

import android.annotation.SuppressLint
import android.bluetooth.BluetoothAdapter
import android.bluetooth.BluetoothDevice
import android.bluetooth.BluetoothSocket
import android.content.Context
import android.content.pm.PackageManager
import android.os.Build
import android.util.Log
import androidx.core.content.ContextCompat
import java.io.IOException
import java.util.UUID

class BluetoothConnectionManager(private val context: Context) {

    companion object {
        private const val TAG = "BluetoothConnManager"
        private val SPP_UUID: UUID = UUID.fromString("00001101-0000-1000-8000-00805F9B34FB")
    }

    private var socket: BluetoothSocket? = null

    private fun hasPermission(permission: String): Boolean {
        return ContextCompat.checkSelfPermission(context, permission) == PackageManager.PERMISSION_GRANTED
    }

    @SuppressLint("MissingPermission")
    fun connectToDevice(address: String): BluetoothSocket? {
        // Permission check
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            if (!hasPermission(android.Manifest.permission.BLUETOOTH_CONNECT)) {
                Log.e(TAG, "BLUETOOTH_CONNECT permission missing")
                return null
            }
        }

        val adapter = BluetoothAdapter.getDefaultAdapter()
        if (adapter == null) {
            Log.e(TAG, "Bluetooth Adapter not found")
            return null
        }
        
        Log.d(TAG, "Selected device address: $address")
        val device: BluetoothDevice = try {
            adapter.getRemoteDevice(address)
        } catch (e: Exception) {
            Log.e(TAG, "Invalid device address: $address", e)
            return null
        }

        return try {
            Log.d(TAG, "Creating RFCOMM socket for device: ${device.name ?: "Unknown"}")
            socket = device.createRfcommSocketToServiceRecord(SPP_UUID)
            Log.d(TAG, "Socket created successfully")
            
            Log.d(TAG, "Connecting to ESP32...")
            socket?.connect()
            Log.d(TAG, "Bluetooth connected successfully")
            socket
        } catch (e: SecurityException) {
            Log.e(TAG, "Permission denied (SecurityException): ${e.message}")
            closeConnection()
            null
        } catch (e: IOException) {
            Log.e(TAG, "Bluetooth connection failed (IOException): ${e.message}")
            closeConnection()
            null
        } catch (e: Exception) {
            Log.e(TAG, "Unexpected error during connection: ${e.message}")
            closeConnection()
            null
        }
    }

    fun closeConnection() {
        try {
            socket?.close()
        } catch (e: IOException) {
            e.printStackTrace()
        } finally {
            socket = null
        }
    }

    fun isConnected(): Boolean {
        return socket?.isConnected ?: false
    }
}
