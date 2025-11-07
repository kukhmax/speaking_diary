package com.speakingdiary.ui.screens

import android.media.MediaRecorder
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import com.speakingdiary.network.ApiClient
import java.io.File

@Composable
fun RecordScreen(onBack: () -> Unit) {
    val ctx = LocalContext.current
    var recorder by remember { mutableStateOf<MediaRecorder?>(null) }
    var outputFile by remember { mutableStateOf<File?>(null) }
    var isRecording by remember { mutableStateOf(false) }
    var transcribed by remember { mutableStateOf("") }
    var error by remember { mutableStateOf<String?>(null) }

    fun startRecording() {
        try {
            val file = File.createTempFile("recording", ".webm", ctx.cacheDir)
            outputFile = file
            val r = MediaRecorder()
            r.setAudioSource(MediaRecorder.AudioSource.MIC)
            r.setOutputFormat(MediaRecorder.OutputFormat.THREE_GPP)
            r.setAudioEncoder(MediaRecorder.AudioEncoder.AMR_NB)
            r.setOutputFile(file.absolutePath)
            r.prepare()
            r.start()
            recorder = r
            isRecording = true
            error = null
        } catch (e: Exception) {
            error = e.message
        }
    }

    fun stopRecording() {
        try {
            recorder?.apply { stop(); reset(); release() }
        } catch (_: Exception) {}
        recorder = null
        isRecording = false
    }

    suspend fun transcribe() {
        val f = outputFile ?: return
        try {
            val resp = ApiClient.transcribeAudio(f, language = "auto")
            transcribed = resp.text
        } catch (e: Exception) {
            error = e.message
        }
    }

    Scaffold(topBar = { TopAppBar(title = { Text("Record") }) }) { p ->
        Column(Modifier.fillMaxSize().padding(p).padding(16.dp)) {
            if (error != null) Text(text = "Ошибка: ${error}")
            Text(text = if (isRecording) "Идет запись..." else "Готово к записи")
            Button(onClick = {
                if (!isRecording) startRecording() else stopRecording()
            }) { Text(text = if (!isRecording) "Начать запись" else "Остановить запись") }
            var trigger by remember { mutableStateOf(0) }
            Button(onClick = {
                if (isRecording) stopRecording()
                trigger++
            }) { Text(text = "Отправить на распознавание") }
            // Side-effect triggers when button pressed, handled via LaunchedEffect
            LaunchedEffect(trigger) {
                if (trigger > 0) transcribe()
            }
            if (transcribed.isNotBlank()) {
                Text(text = "Распознано: $transcribed", modifier = Modifier.padding(top = 12.dp))
            }
        }
    }
}