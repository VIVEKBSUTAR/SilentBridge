package com.example.gloves

import android.content.Context
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material.icons.filled.Close
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import org.json.JSONObject

@OptIn(ExperimentalMaterial3Api::class, ExperimentalLayoutApi::class)
@Composable
fun ManageWordsScreen(onBack: () -> Unit) {
    val context = LocalContext.current
    val prefs = context.getSharedPreferences("silentbridge_feedback", Context.MODE_PRIVATE)

    // Load model words from label_map.json
    val modelWords = remember {
        try {
            // Attempt to load with both possible names found in assets
            val json = try {
                context.assets.open("label_map.json").bufferedReader().use { it.readText() }
            } catch (e: Exception) {
                context.assets.open("label_map (1).json").bufferedReader().use { it.readText() }
            }
            val obj = JSONObject(json)
            val list = mutableListOf<String>()
            val keys = obj.keys()
            while (keys.hasNext()) {
                list.add(keys.next().uppercase())
            }
            list.sorted()
        } catch (e: Exception) {
            emptyList()
        }
    }

    // Load and save custom words from SharedPreferences
    var customWords by remember {
        mutableStateOf(
            prefs.getString("custom_words", "")
                ?.split(",")
                ?.map { it.trim().uppercase() }
                ?.filter { it.isNotBlank() }
                ?: emptyList()
        )
    }

    fun saveCustomWords(words: List<String>) {
        prefs.edit().putString("custom_words", words.joinToString(",")).apply()
        customWords = words
    }

    var newWordInput by remember { mutableStateOf("") }
    var errorMessage by remember { mutableStateOf<String?>(null) }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Manage Words") },
                navigationIcon = {
                    IconButton(onClick = onBack) {
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
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(20.dp)
        ) {

            // Model words section
            Text(
                "Words from model (${modelWords.size}):",
                style = MaterialTheme.typography.titleMedium
            )
            if (modelWords.isEmpty()) {
                Text(
                    "Could not load label_map.json",
                    color = MaterialTheme.colorScheme.error,
                    fontSize = 13.sp
                )
            } else {
                FlowRow(
                    horizontalArrangement = Arrangement.spacedBy(8.dp),
                    verticalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    modelWords.forEach { word ->
                        AssistChip(
                            onClick = {},
                            label = { Text(word, fontSize = 13.sp) }
                        )
                    }
                }
            }

            HorizontalDivider()

            // Custom words section
            Text(
                "Your custom words (${customWords.size}):",
                style = MaterialTheme.typography.titleMedium
            )

            if (customWords.isEmpty()) {
                Text(
                    "No custom words added yet.",
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    fontSize = 13.sp
                )
            } else {
                FlowRow(
                    horizontalArrangement = Arrangement.spacedBy(8.dp),
                    verticalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    customWords.forEach { word ->
                        InputChip(
                            selected = false,
                            onClick = {},
                            label = { Text(word, fontSize = 13.sp) },
                            trailingIcon = {
                                IconButton(
                                    onClick = {
                                        saveCustomWords(customWords - word)
                                    },
                                    modifier = Modifier.size(18.dp)
                                ) {
                                    Icon(
                                        Icons.Default.Close,
                                        contentDescription = "Remove $word",
                                        modifier = Modifier.size(14.dp)
                                    )
                                }
                            }
                        )
                    }
                }
            }

            HorizontalDivider()

            // Add new word section
            Text(
                "Add a word:",
                style = MaterialTheme.typography.titleMedium
            )

            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(8.dp),
                modifier = Modifier.fillMaxWidth()
            ) {
                OutlinedTextField(
                    value = newWordInput,
                    onValueChange = {
                        newWordInput = it
                        errorMessage = null
                    },
                    placeholder = { Text("Type new word...") },
                    singleLine = true,
                    modifier = Modifier.weight(1f)
                )
                Button(
                    onClick = {
                        val clean = newWordInput.trim().uppercase()
                        when {
                            clean.isBlank() -> {
                                errorMessage = "Word cannot be empty"
                            }
                            clean in modelWords -> {
                                errorMessage = "$clean is already in the model"
                            }
                            clean in customWords -> {
                                errorMessage = "$clean already added"
                            }
                            else -> {
                                saveCustomWords(customWords + clean)
                                newWordInput = ""
                                errorMessage = null
                            }
                        }
                    }
                ) {
                    Text("Add")
                }
            }

            errorMessage?.let {
                Text(it, color = MaterialTheme.colorScheme.error, fontSize = 13.sp)
            }

            // Note to user
            Card(
                colors = CardDefaults.cardColors(
                    containerColor = MaterialTheme.colorScheme.surfaceVariant
                )
            ) {
                Text(
                    "Note: Only add words the model was trained to recognise. " +
                    "Adding words not in the model will not make the model recognise them — " +
                    "the model must be retrained for that.",
                    fontSize = 12.sp,
                    modifier = Modifier.padding(12.dp),
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        }
    }
}
