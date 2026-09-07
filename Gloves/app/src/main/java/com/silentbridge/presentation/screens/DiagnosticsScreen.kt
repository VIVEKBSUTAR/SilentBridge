package com.silentbridge.presentation.screens

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.silentbridge.domain.model.SensorFrame
import com.silentbridge.presentation.viewmodel.MainViewModel

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun DiagnosticsScreen(
    viewModel: MainViewModel,
    onNavigateBack: () -> Unit
) {
    val uiState by viewModel.uiState.collectAsState()
    val sensorFrame = uiState.latestSensorFrame ?: SensorFrame()

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Sensor Diagnostics") },
                navigationIcon = {
                    IconButton(onClick = onNavigateBack) {
                        Icon(Icons.Default.ArrowBack, contentDescription = "Back")
                    }
                }
            )
        }
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(16.dp)
                .verticalScroll(rememberScrollState())
        ) {
            Text("Connection: ${uiState.connectionState}", style = MaterialTheme.typography.titleMedium)
            Spacer(modifier = Modifier.height(16.dp))

            SensorSection("Finger Sensors") {
                SensorRow("Thumb", sensorFrame.thumb.toString())
                SensorRow("Index", sensorFrame.index.toString())
                SensorRow("Middle", sensorFrame.middle.toString())
                SensorRow("Ring", sensorFrame.ring.toString())
                SensorRow("Little", sensorFrame.little.toString())
            }

            Spacer(modifier = Modifier.height(16.dp))

            SensorSection("Accelerometer") {
                SensorRow("AX", sensorFrame.ax.toString())
                SensorRow("AY", sensorFrame.ay.toString())
                SensorRow("AZ", sensorFrame.az.toString())
            }

            Spacer(modifier = Modifier.height(16.dp))

            SensorSection("Gyroscope") {
                SensorRow("GX", sensorFrame.gx.toString())
                SensorRow("GY", sensorFrame.gy.toString())
                SensorRow("GZ", sensorFrame.gz.toString())
            }

            Spacer(modifier = Modifier.height(16.dp))

            SensorSection("Orientation") {
                SensorRow("Pitch", sensorFrame.pitch.toString())
                SensorRow("Roll", sensorFrame.roll.toString())
            }
        }
    }
}

@Composable
fun SensorSection(title: String, content: @Composable ColumnScope.() -> Unit) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        elevation = CardDefaults.cardElevation(defaultElevation = 2.dp)
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text(text = title, style = MaterialTheme.typography.titleSmall)
            Divider(modifier = Modifier.padding(vertical = 8.dp))
            content()
        }
    }
}

@Composable
fun SensorRow(label: String, value: String) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween
    ) {
        Text(text = label, style = MaterialTheme.typography.bodyMedium)
        Text(text = value, style = MaterialTheme.typography.bodyMedium)
    }
}
