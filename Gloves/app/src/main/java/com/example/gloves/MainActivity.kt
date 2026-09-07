package com.example.gloves

import android.Manifest
import android.os.Build
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Close
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.silentbridge.navigation.Screen
import com.silentbridge.presentation.screens.DeviceScreen
import com.silentbridge.presentation.screens.DiagnosticsScreen
import com.silentbridge.presentation.screens.HomeScreen
import com.silentbridge.presentation.screens.StatsScreen
import com.silentbridge.presentation.screens.ManageWordsScreen
import com.silentbridge.presentation.viewmodel.MainViewModel
import com.silentbridge.presentation.viewmodel.ViewModelFactory

class MainActivity : ComponentActivity() {

    private val requestPermissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions()
    ) { permissions ->
        // Handle permissions if needed
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        
        requestPermissions()

        setContent {
            MaterialTheme {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background
                ) {
                    val viewModel: MainViewModel = viewModel(
                        factory = ViewModelFactory(applicationContext)
                    )
                    SilentBridgeApp(viewModel)
                }
            }
        }
    }

    private fun requestPermissions() {
        val permissions = mutableListOf<String>()
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            permissions.add(Manifest.permission.BLUETOOTH_SCAN)
            permissions.add(Manifest.permission.BLUETOOTH_CONNECT)
        } else {
            permissions.add(Manifest.permission.BLUETOOTH)
            permissions.add(Manifest.permission.BLUETOOTH_ADMIN)
            permissions.add(Manifest.permission.ACCESS_FINE_LOCATION)
        }
        requestPermissionLauncher.launch(permissions.toTypedArray())
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SilentBridgeApp(viewModel: MainViewModel) {
    val navController = rememberNavController()
    val context = androidx.compose.ui.platform.LocalContext.current
    
    val prefs = remember {
        context.getSharedPreferences("silentbridge_feedback", android.content.Context.MODE_PRIVATE)
    }
    val savedMode = remember { prefs.getString("trigger_mode", null) }
    var showModeDialog by remember { mutableStateOf(true) }
    var selectedMode by remember { mutableStateOf(savedMode) }

    if (showModeDialog) {
        AlertDialog(
            onDismissRequest = { /* force choice, no dismiss */ },
            title = { Text("How should sentences be formed?") },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                    Card(
                        onClick = { selectedMode = "auto" },
                        border = if (selectedMode == "auto")
                            BorderStroke(2.dp, MaterialTheme.colorScheme.primary) else null
                    ) {
                        Column(Modifier.padding(16.dp)) {
                            Text("Auto", style = MaterialTheme.typography.titleMedium)
                            Text(
                                "Sentence forms automatically after 2 seconds of silence, or after 10 words.",
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                        }
                    }

                    Card(
                        onClick = { selectedMode = "manual" },
                        border = if (selectedMode == "manual")
                            BorderStroke(2.dp, MaterialTheme.colorScheme.primary) else null
                    ) {
                        Column(Modifier.padding(16.dp)) {
                            Text("Manual", style = MaterialTheme.typography.titleMedium)
                            Text(
                                "Tap the Done button when you have finished signing all your words.",
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                        }
                    }
                }
            },
            confirmButton = {
                Button(
                    onClick = {
                        selectedMode?.let { mode ->
                            viewModel.saveTriggerMode(mode)
                            showModeDialog = false
                        }
                    },
                    enabled = selectedMode != null
                ) { Text("Continue") }
            }
        )
    }

    NavHost(navController = navController, startDestination = Screen.Home.route) {
        composable(Screen.Home.route) {
            HomeScreen(
                viewModel = viewModel,
                onNavigateToDevices = { navController.navigate(Screen.Devices.route) },
                onNavigateToDiagnostics = { navController.navigate(Screen.Diagnostics.route) },
                onNavigateToStats = { navController.navigate(Screen.Stats.route) },
                onNavigateToManageWords = { navController.navigate(Screen.ManageWords.route) }
            )
        }
        composable(Screen.Devices.route) {
            DeviceScreen(
                viewModel = viewModel,
                onNavigateBack = { 
                    viewModel.refreshDevices()
                    navController.popBackStack() 
                }
            )
        }
        composable(Screen.Diagnostics.route) {
            DiagnosticsScreen(
                viewModel = viewModel,
                onNavigateBack = { navController.popBackStack() }
            )
        }
        composable(Screen.Stats.route) {
            StatsScreen(
                viewModel = viewModel,
                onNavigateBack = { navController.popBackStack() }
            )
        }
        composable(Screen.ManageWords.route) {
            ManageWordsScreen(
                viewModel = viewModel,
                onNavigateBack = {
                    viewModel.loadLabels()
                    navController.popBackStack() 
                }
            )
        }
    }
}
