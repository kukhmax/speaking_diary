package com.speakingdiary.ui.screens

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.speakingdiary.network.ApiClient

@Composable
fun ReviewScreen(onBack: () -> Unit) {
    // In a real app, get ID from NavBackStackEntry arguments
    var original by remember { mutableStateOf("") }
    var corrected by remember { mutableStateOf("") }
    var explanations by remember { mutableStateOf(listOf<String>()) }
    var error by remember { mutableStateOf<String?>(null) }

    LaunchedEffect(Unit) {
        // Placeholder: could retrieve entry ID and load
        try {
            val review = ApiClient.review(text = original.ifBlank { "Hello world" }, language = null, uiLanguage = "ru")
            corrected = review.corrected_text
            explanations = review.explanations
        } catch (e: Exception) {
            error = e.message
        }
    }

    Scaffold(topBar = { TopAppBar(title = { Text("Review") }) }) { p ->
        Column(Modifier.fillMaxSize().padding(p).padding(16.dp)) {
            if (error != null) {
                Text(text = error!!)
            }
            Text(text = "Original: $original")
            Text(text = "Corrected: $corrected")
            explanations.forEach { Text(text = "• $it") }
            Button(onClick = onBack, modifier = Modifier.padding(top = 16.dp)) { Text(text = "Назад") }
        }
    }
}