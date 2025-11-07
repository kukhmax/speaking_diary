package com.speakingdiary.ui.screens

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Button
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.Scaffold
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.speakingdiary.R
import com.speakingdiary.network.ApiClient

@Composable
fun HomeScreen(
    onOpenDetails: (String) -> Unit,
    onGoRecord: () -> Unit,
    onGoSettings: () -> Unit
) {
    var error by remember { mutableStateOf<String?>(null) }
    var entries by remember { mutableStateOf(listOf<ApiClient.EntryDto>()) }

    LaunchedEffect(Unit) {
        error = null
        try {
            val resp = ApiClient.getEntries(page = 1, perPage = 20)
            entries = resp.entries
        } catch (e: Exception) {
            error = e.message ?: "Ошибка загрузки записей. Возможно, требуется токен."
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(title = { Text(text = stringResource(id = R.string.home_title)) })
        },
        bottomBar = {
            Row(Modifier.padding(12.dp), horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                Button(onClick = onGoRecord) { Text(stringResource(id = R.string.record_title)) }
                Button(onClick = onGoSettings) { Text(stringResource(id = R.string.settings_title)) }
            }
        }
    ) { padding ->
        Column(Modifier.padding(padding)) {
            if (error != null) {
                Text(text = error!!, modifier = Modifier.padding(12.dp))
            }
            LazyColumn(Modifier.fillMaxWidth()) {
                items(entries) { item ->
                    Row(
                        Modifier
                            .fillMaxWidth()
                            .padding(horizontal = 12.dp, vertical = 8.dp),
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        Text(text = item.text)
                        Button(onClick = { onOpenDetails(item.id.toString()) }) {
                            Text(text = stringResource(id = R.string.more_details))
                        }
                    }
                }
            }
        }
    }
}