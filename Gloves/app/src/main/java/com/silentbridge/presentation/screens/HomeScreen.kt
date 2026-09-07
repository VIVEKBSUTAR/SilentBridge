package com.silentbridge.presentation.screens

import android.Manifest
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.animation.animateContentSize
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.Language
import androidx.compose.material.icons.filled.MoreVert
import androidx.compose.material.icons.filled.Translate
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.silentbridge.domain.model.ConnectionState
import com.silentbridge.gesture.InferenceState
import com.silentbridge.listen.TranslationManager
import com.silentbridge.presentation.viewmodel.MainViewModel

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun HomeScreen(
    viewModel: MainViewModel,
    onNavigateToDevices: () -> Unit,
    onNavigateToDiagnostics: () -> Unit,
    onNavigateToStats: () -> Unit,
    onNavigateToManageWords: () -> Unit
) {
    val uiState by viewModel.uiState.collectAsState()
    var showMenu by remember { mutableStateOf(false) }
    var showLanguageDialog by remember { mutableStateOf(false) }
    var showListenLanguagePicker by remember { mutableStateOf(false) }

    // Microphone permission launcher
    val micPermissionLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { granted ->
        if (granted) viewModel.startListening()
    }

    val languages = listOf(
        "en" to "English",
        "hi" to "Hindi (हिंदी)",
        "mr" to "Marathi (मराठी)",
        "gu" to "Gujarati (ગુજરાતી)",
        "ta" to "Tamil (தமிழ்)",
        "te" to "Telugu (తెలుగు)",
        "kn" to "Kannada (ಕನ್ನಡ)"
    )

    if (showLanguageDialog) {
        AlertDialog(
            onDismissRequest = { showLanguageDialog = false },
            title = { Text("Select Output Language") },
            text = {
                Column {
                    languages.forEach { (code, name) ->
                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(vertical = 8.dp),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            RadioButton(
                                selected = uiState.targetLanguageCode == code,
                                onClick = {
                                    viewModel.setTargetLanguage(code)
                                    showLanguageDialog = false
                                }
                            )
                            Text(
                                text = name,
                                modifier = Modifier.padding(start = 8.dp),
                                style = MaterialTheme.typography.bodyLarge
                            )
                        }
                    }
                }
            },
            confirmButton = {
                TextButton(onClick = { showLanguageDialog = false }) { Text("Cancel") }
            }
        )
    }

    if (showListenLanguagePicker) {
        AlertDialog(
            onDismissRequest = { showListenLanguagePicker = false },
            title = { Text("Select Listening Language") },
            text = {
                Column(modifier = Modifier.verticalScroll(rememberScrollState())) {
                    TranslationManager.SUPPORTED_LANGUAGES.forEach { (code, label) ->
                        TextButton(
                            onClick = {
                                viewModel.setListenLanguage(code)
                                showListenLanguagePicker = false
                            },
                            modifier = Modifier.fillMaxWidth()
                        ) {
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.SpaceBetween
                            ) {
                                Text(label)
                                if (uiState.listenLanguage == code) {
                                    Text("✓", color = MaterialTheme.colorScheme.primary)
                                }
                            }
                        }
                    }
                }
            },
            confirmButton = {
                TextButton(onClick = { showListenLanguagePicker = false }) { Text("Close") }
            }
        )
    }

    val context = androidx.compose.ui.platform.LocalContext.current

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("SilentBridge") },
                actions = {
                    IconButton(onClick = { showLanguageDialog = true }) {
                        Icon(Icons.Default.Translate, contentDescription = "Language")
                    }
                    IconButton(onClick = { showMenu = !showMenu }) {
                        Icon(Icons.Default.MoreVert, contentDescription = "More")
                    }
                    DropdownMenu(
                        expanded = showMenu,
                        onDismissRequest = { showMenu = false }
                    ) {
                        DropdownMenuItem(
                            text = { Text("Diagnostics") },
                            onClick = {
                                showMenu = false
                                onNavigateToDiagnostics()
                            }
                        )
                        DropdownMenuItem(
                            text = { Text("Prediction Stats") },
                            onClick = {
                                showMenu = false
                                onNavigateToStats()
                            }
                        )
                        DropdownMenuItem(
                            text = { Text("Export Dataset (${uiState.feedbackCount})") },
                            onClick = {
                                showMenu = false
                                viewModel.exportDataset()
                            }
                        )
                        DropdownMenuItem(
                            text = { Text("Manage Words") },
                            onClick = {
                                showMenu = false
                                onNavigateToManageWords()
                            }
                        )
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
                .verticalScroll(rememberScrollState()),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            // 1. Connection Status (Top)
            Row(verticalAlignment = Alignment.CenterVertically) {
                val color = when (uiState.connectionState) {
                    ConnectionState.CONNECTED -> Color.Green
                    ConnectionState.CONNECTING -> Color.Yellow
                    ConnectionState.DISCONNECTED -> Color.Red
                    ConnectionState.ERROR -> Color.Red
                    ConnectionState.SEARCHING -> Color.Blue
                }
                Surface(
                    modifier = Modifier.size(12.dp),
                    shape = CircleShape,
                    color = color
                ) {}
                Spacer(modifier = Modifier.width(8.dp))
                Text(text = "Glove: ${uiState.connectionState.name}", style = MaterialTheme.typography.labelMedium)
            }

            if (uiState.isDownloadingModel) {
                LinearProgressIndicator(modifier = Modifier.fillMaxWidth().padding(vertical = 8.dp))
                Text("Downloading language pack...", style = MaterialTheme.typography.labelSmall)
            }

            if (uiState.connectionState != ConnectionState.CONNECTED) {
                Spacer(modifier = Modifier.height(16.dp))
                Button(onClick = onNavigateToDevices, modifier = Modifier.fillMaxWidth()) {
                    Text("Connect Glove")
                }
            }

            Spacer(modifier = Modifier.height(24.dp))

            // 2. Middle Section (The Focal Point - Sign Translation)
            if (uiState.isFormingSentence) {
                Column(horizontalAlignment = Alignment.CenterHorizontally, modifier = Modifier.padding(16.dp)) {
                    CircularProgressIndicator()
                    Spacer(modifier = Modifier.height(16.dp))
                    Text("AI is forming sentence...", style = MaterialTheme.typography.labelMedium, color = Color.Gray)
                }
            } else if (uiState.formedSentence != null) {
                Card(
                    modifier = Modifier
                        .fillMaxWidth()
                        .animateContentSize(),
                    shape = RoundedCornerShape(24.dp),
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant),
                    elevation = CardDefaults.cardElevation(defaultElevation = 2.dp)
                ) {
                    Column(Modifier.padding(24.dp), horizontalAlignment = Alignment.CenterHorizontally) {
                        if (uiState.translatedSentence != null && uiState.targetLanguageCode != "en") {
                            Text(
                                text = uiState.translatedSentence!!,
                                style = MaterialTheme.typography.headlineMedium,
                                fontWeight = FontWeight.Bold,
                                color = MaterialTheme.colorScheme.primary,
                                textAlign = TextAlign.Center
                            )
                            Spacer(modifier = Modifier.height(16.dp))
                            HorizontalDivider(modifier = Modifier.padding(horizontal = 32.dp))
                            Spacer(modifier = Modifier.height(16.dp))
                        }
                        
                        Text(
                            text = uiState.formedSentence!!,
                            style = if (uiState.translatedSentence == null) MaterialTheme.typography.headlineMedium else MaterialTheme.typography.titleMedium,
                            fontWeight = if (uiState.translatedSentence == null) FontWeight.Bold else FontWeight.Normal,
                            color = if (uiState.translatedSentence == null) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.onSurfaceVariant,
                            textAlign = TextAlign.Center
                        )

                        Row(Modifier.padding(top = 24.dp), horizontalArrangement = Arrangement.spacedBy(16.dp)) {
                            Button(onClick = { viewModel.speakSentence() }, modifier = Modifier.weight(1f)) {
                                Text("Speak")
                            }
                            OutlinedButton(onClick = { viewModel.clearSentence(); viewModel.clearBuffer() }) {
                                Text("Clear")
                            }
                        }
                    }
                }
            }

            // Word Buffer right below the focal point
            if (uiState.wordBuffer.isNotEmpty()) {
                LazyRow(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(vertical = 16.dp),
                    horizontalArrangement = Arrangement.Center
                ) {
                    itemsIndexed(uiState.wordBuffer) { index, word ->
                        AssistChip(
                            onClick = { viewModel.removeWordFromBuffer(index) },
                            label = { Text(word, fontSize = 16.sp) },
                            trailingIcon = { Icon(Icons.Default.Close, null, Modifier.size(16.dp)) },
                            modifier = Modifier.padding(horizontal = 4.dp),
                            shape = RoundedCornerShape(16.dp)
                        )
                    }
                }
            }

            Spacer(modifier = Modifier.height(32.dp))

            // 3. Listen Mode Section
            HorizontalDivider(modifier = Modifier.padding(vertical = 8.dp))

            Text(
                text = "Listen Mode",
                style = MaterialTheme.typography.titleMedium,
                modifier = Modifier.align(Alignment.Start)
            )

            Text(
                text = "Let someone speak — their words appear as text for you to read.",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier.align(Alignment.Start)
            )

            Spacer(modifier = Modifier.height(12.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "Show text in: ${uiState.listenLanguageLabel}",
                    style = MaterialTheme.typography.bodyMedium
                )
                OutlinedButton(onClick = { showListenLanguagePicker = true }) {
                    Text("Change")
                }
            }

            Spacer(modifier = Modifier.height(12.dp))

            Button(
                onClick = {
                    if (uiState.isListening) {
                        viewModel.stopListening()
                    } else {
                        if (viewModel.hasMicPermission()) {
                            viewModel.startListening()
                        } else {
                            micPermissionLauncher.launch(Manifest.permission.RECORD_AUDIO)
                        }
                    }
                },
                modifier = Modifier.fillMaxWidth(),
                colors = ButtonDefaults.buttonColors(
                    containerColor = if (uiState.isListening)
                        MaterialTheme.colorScheme.error
                    else
                        Color(0xFF7f77dd)
                ),
                shape = RoundedCornerShape(12.dp),
                contentPadding = PaddingValues(vertical = 14.dp)
            ) {
                if (uiState.isListening) {
                    Row(
                        horizontalArrangement = Arrangement.spacedBy(8.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        CircularProgressIndicator(
                            modifier = Modifier.size(16.dp),
                            strokeWidth = 2.dp,
                            color = Color.White
                        )
                        Text("Listening… (tap to stop)", color = Color.White, fontWeight = FontWeight.Bold)
                    }
                } else {
                    Text("🎤  Listen to Someone", color = Color.White, fontWeight = FontWeight.Bold)
                }
            }

            if (uiState.isTranslating) {
                Row(
                    modifier = Modifier.padding(top = 8.dp),
                    horizontalArrangement = Arrangement.spacedBy(8.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    CircularProgressIndicator(modifier = Modifier.size(14.dp), strokeWidth = 2.dp)
                    Text("Translating…", fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
            }

            uiState.listenError?.let {
                Text(
                    text = it,
                    color = MaterialTheme.colorScheme.error,
                    fontSize = 13.sp,
                    modifier = Modifier.padding(top = 8.dp)
                )
            }

            if (uiState.listenedText != null) {
                Spacer(modifier = Modifier.height(16.dp))
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(16.dp),
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.primaryContainer)
                ) {
                    Column(modifier = Modifier.padding(20.dp)) {
                        val displayText = uiState.translatedListenText ?: uiState.listenedText!!
                        Text(
                            text = displayText,
                            style = MaterialTheme.typography.headlineSmall,
                            fontWeight = FontWeight.Bold,
                            color = MaterialTheme.colorScheme.onPrimaryContainer,
                            textAlign = TextAlign.Center,
                            modifier = Modifier.fillMaxWidth()
                        )

                        if (uiState.translatedListenText != null) {
                            Spacer(modifier = Modifier.height(8.dp))
                            Text(
                                text = "Original: ${uiState.listenedText}",
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onPrimaryContainer.copy(alpha = 0.7f),
                                textAlign = TextAlign.Center,
                                modifier = Modifier.fillMaxWidth()
                            )
                        }
                        
                        Row(modifier = Modifier.padding(top = 16.dp), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                            Button(onClick = { viewModel.speakSentence() }, modifier = Modifier.weight(1f)) {
                                Text("Speak")
                            }
                            OutlinedButton(onClick = { viewModel.clearListenResult() }) {
                                Text("Clear")
                            }
                        }
                    }
                }
            }

            Spacer(modifier = Modifier.height(32.dp))

            // 4. Bottom Section (Sign Controls)
            HorizontalDivider(modifier = Modifier.padding(vertical = 8.dp))
            
            Card(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(vertical = 8.dp),
                colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.secondaryContainer),
                shape = RoundedCornerShape(16.dp)
            ) {
                Column(Modifier.padding(16.dp), horizontalAlignment = Alignment.CenterHorizontally) {
                    if (uiState.gestureResult != null) {
                        Text(text = "Detected Gesture", style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSecondaryContainer)
                        Text(
                            text = uiState.gestureResult!!.gestureName, 
                            style = MaterialTheme.typography.headlineLarge, 
                            color = if (uiState.isWrongFlash) Color.Red else MaterialTheme.colorScheme.onSecondaryContainer,
                            fontWeight = FontWeight.Bold
                        )
                        
                        if (uiState.showFeedbackButtons && !uiState.showCorrectionSelector) {
                            Row(horizontalArrangement = Arrangement.spacedBy(16.dp), modifier = Modifier.padding(top = 16.dp)) {
                                Button(onClick = { viewModel.onFeedbackYes() }, colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF40a02b))) { Text("YES") }
                                Button(onClick = { viewModel.onFeedbackNo() }, colors = ButtonDefaults.buttonColors(containerColor = Color(0xFFe64553))) { Text("NO") }
                            }
                        }
                    } else {
                        val statusText = when(uiState.inferenceState) {
                            InferenceState.READY -> "Ready to Sign"
                            InferenceState.CALIBRATING -> "Calibrating (Keep Still)..."
                            InferenceState.RECORDING -> "Recording Gesture..."
                            InferenceState.PREPROCESSING, InferenceState.MODEL_INFERENCE -> "Processing AI..."
                            InferenceState.DISCONNECTED -> "Connect Glove first"
                            else -> "Waiting..."
                        }
                        Text(
                            text = statusText,
                            style = MaterialTheme.typography.bodyLarge,
                            color = MaterialTheme.colorScheme.onSecondaryContainer
                        )
                    }
                }
            }

            if (uiState.showCorrectionSelector) {
                LazyVerticalGrid(columns = GridCells.Fixed(3), modifier = Modifier.height(150.dp).padding(top = 8.dp)) {
                    items(uiState.modelLabels + uiState.customLabels) { label ->
                        FilterChip(selected = false, onClick = { viewModel.submitCorrectedLabel(label) }, label = { Text(label, fontSize = 10.sp) })
                    }
                }
            }

            Row(Modifier.padding(top = 16.dp).fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                if (uiState.inferenceState == InferenceState.READY) {
                    Button(
                        onClick = { viewModel.startGestureSession() },
                        enabled = uiState.connectionState == ConnectionState.CONNECTED,
                        modifier = Modifier.weight(1f),
                        contentPadding = PaddingValues(vertical = 16.dp),
                        shape = RoundedCornerShape(12.dp)
                    ) { Text("START SIGNING", fontSize = 16.sp, fontWeight = FontWeight.Bold) }
                }
                
                if (viewModel.getTriggerModePublic() == "manual" && uiState.wordBuffer.isNotEmpty()) {
                    Button(
                        onClick = { viewModel.triggerSentenceFormation() }, 
                        colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.primary),
                        modifier = Modifier.weight(1f),
                        contentPadding = PaddingValues(vertical = 16.dp),
                        shape = RoundedCornerShape(12.dp)
                    ) { Text("FORM SENTENCE", fontSize = 16.sp, fontWeight = FontWeight.Bold) }
                }
            }
        }
    }
}
