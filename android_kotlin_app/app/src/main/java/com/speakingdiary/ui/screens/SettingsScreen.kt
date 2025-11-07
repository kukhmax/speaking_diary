package com.speakingdiary.ui.screens

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import com.speakingdiary.pref.Prefs
import com.speakingdiary.network.ApiClient

@Composable
fun SettingsScreen(onBack: () -> Unit) {
    val ctx = LocalContext.current
    var baseUrl by remember { mutableStateOf(Prefs.getBaseUrl(ctx) ?: "") }
    var token by remember { mutableStateOf(Prefs.getToken(ctx) ?: "") }
    var uiLang by remember { mutableStateOf(Prefs.getUiLanguage(ctx)) }
    var saved by remember { mutableStateOf(false) }

    fun save() {
        Prefs.setBaseUrl(ctx, baseUrl)
        Prefs.setToken(ctx, token)
        Prefs.setUiLanguage(ctx, uiLang)
        ApiClient.configure(baseUrl, token)
        saved = true
    }

    Scaffold(topBar = { TopAppBar(title = { Text("Settings") }) }) { p ->
        Column(Modifier.fillMaxSize().padding(p).padding(16.dp)) {
            OutlinedTextField(value = baseUrl, onValueChange = { baseUrl = it }, label = { Text("Base URL") })
            OutlinedTextField(value = token, onValueChange = { token = it }, label = { Text("Access Token") })
            OutlinedTextField(value = uiLang, onValueChange = { uiLang = it }, label = { Text("UI Language (ru/en/...) ") })
            Button(onClick = { save() }, modifier = Modifier.padding(top = 12.dp)) { Text(text = "Сохранить") }
            if (saved) Text(text = "Сохранено", modifier = Modifier.padding(top = 8.dp))
            Button(onClick = onBack, modifier = Modifier.padding(top = 16.dp)) { Text(text = "Назад") }
        }
    }
}