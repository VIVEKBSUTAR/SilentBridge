package com.silentbridge.presentation.screens

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.silentbridge.presentation.viewmodel.MainViewModel

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun StatsScreen(
    viewModel: MainViewModel,
    onNavigateBack: () -> Unit
) {
    val stats = remember { viewModel.getStats() }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Prediction Stats") },
                navigationIcon = {
                    IconButton(onClick = onNavigateBack) {
                        Icon(Icons.Default.ArrowBack, contentDescription = "Back")
                    }
                }
            )
        }
    ) { padding ->
        LazyColumn(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            item {
                Row(
                    modifier = Modifier.fillMaxWidth().padding(bottom = 8.dp),
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Text("Gesture", style = MaterialTheme.typography.titleSmall, modifier = Modifier.weight(2f))
                    Text("✓", style = MaterialTheme.typography.titleSmall, modifier = Modifier.weight(1f))
                    Text("✗", style = MaterialTheme.typography.titleSmall, modifier = Modifier.weight(1f))
                    Text("Penalty", style = MaterialTheme.typography.titleSmall, modifier = Modifier.weight(1.5f))
                }
                Divider()
            }

            items(stats.toList()) { (gesture, counts) ->
                val correct = counts.first
                val wrong = counts.second
                val total = correct + wrong
                val penalty = if (total > 0) (wrong.toFloat() / 20 * 100).toInt() else 0

                Row(
                    modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp),
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Text(gesture, modifier = Modifier.weight(2f), fontSize = 14.sp)
                    Text(correct.toString(), modifier = Modifier.weight(1f), color = Color(0xFF40a02b), fontSize = 14.sp)
                    Text(wrong.toString(), modifier = Modifier.weight(1f), color = Color(0xFFe64553), fontSize = 14.sp)
                    Text("$penalty%", modifier = Modifier.weight(1.5f), color = if (penalty > 0) Color(0xFFfab387) else Color.Gray, fontSize = 14.sp)
                }
            }
            
            if (stats.isEmpty()) {
                item {
                    Box(modifier = Modifier.fillMaxSize().padding(top = 32.dp)) {
                        Text("No feedback data yet.", style = MaterialTheme.typography.bodyMedium, color = Color.Gray)
                    }
                }
            }
        }
    }
}
