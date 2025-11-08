package com.speakingdiary.ui.viewmodel

import android.app.Application
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.speakingdiary.data.repository.DiaryRepository
import com.speakingdiary.data.repository.ReviewResult
import com.speakingdiary.data.model.Entry
import com.speakingdiary.utils.AudioRecorder
import com.speakingdiary.utils.Constants
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.io.File

class DiaryViewModel(private val app: Application) : ViewModel() {
    private val retrofit = Retrofit.Builder()
        .baseUrl(Constants.BASE_URL)
        .addConverterFactory(GsonConverterFactory.create())
        .build()
    
    private val repository = DiaryRepository(
        retrofit.create(com.speakingdiary.data.api.ApiService::class.java)
    )

    private val cacheDir = File(app.cacheDir, "audio").apply { mkdirs() }
    private val audioFile = File(cacheDir, Constants.AUDIO_FILE_NAME)
    private val recorder = AudioRecorder(audioFile)

    // UI State
    private val _uiState = MutableStateFlow(DiaryUiState())
    val uiState: StateFlow<DiaryUiState> = _uiState.asStateFlow()

    // Events
    private val _navigateToEntry = MutableSharedFlow<Entry>()
    val navigateToEntry: SharedFlow<Entry> = _navigateToEntry.asSharedFlow()

    init {
        loadEntries()
        checkBackendHealth()
    }

    fun onLanguageSelected(language: String) {
        _uiState.value = _uiState.value.copy(selectedLanguage = language)
    }

    fun toggleRecording() {
        if (recorder.isRecording) {
            stopRecording()
        } else {
            startRecording()
        }
    }

    private fun startRecording() {
        viewModelScope.launch {
            recorder.start()
                .onSuccess { 
                    _uiState.value = _uiState.value.copy(isRecording = true)
                }
                .onFailure { error ->
                    _uiState.value = _uiState.value.copy(error = error.message)
                }
        }
    }

    private fun stopRecording() {
        viewModelScope.launch {
            recorder.stop()
                .onSuccess { audioFile ->
                    _uiState.value = _uiState.value.copy(isRecording = false)
                    transcribeAndSave(audioFile)
                }
                .onFailure { error ->
                    _uiState.value = _uiState.value.copy(
                        isRecording = false,
                        error = error.message
                    )
                }
        }
    }

    private fun transcribeAndSave(audioFile: File) {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true)
            
            repository.transcribeAudio(audioFile, uiState.value.selectedLanguage)
                .onSuccess { transcribedText ->
                    audioFile.delete() // Очистка временного файла
                    saveEntry(transcribedText)
                }
                .onFailure { error ->
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        error = "Transcription failed: ${error.message}"
                    )
                }
        }
    }

    private fun saveEntry(text: String) {
        viewModelScope.launch {
            repository.createEntry(text, uiState.value.selectedLanguage, 0.0)
                .onSuccess { entry ->
                    loadEntries() // Обновить список
                    _navigateToEntry.emit(entry) // Открыть детали
                }
                .onFailure { error ->
                    _uiState.value = _uiState.value.copy(error = error.message)
                }
                .also {
                    _uiState.value = _uiState.value.copy(isLoading = false)
                }
        }
    }

    private fun loadEntries() {
        viewModelScope.launch {
            repository.getEntries()
                .onSuccess { entries ->
                    _uiState.value = _uiState.value.copy(entries = entries)
                }
                .onFailure { error ->
                    _uiState.value = _uiState.value.copy(error = error.message)
                }
        }
    }

    private fun checkBackendHealth() {
        viewModelScope.launch {
            repository.healthCheck()
                .onSuccess { isHealthy ->
                    _uiState.value = _uiState.value.copy(isBackendHealthy = isHealthy)
                }
                .onFailure {
                    _uiState.value = _uiState.value.copy(isBackendHealthy = false)
                }
        }
    }

    fun dismissError() {
        _uiState.value = _uiState.value.copy(error = null)
    }

    fun playEntryAudio(entry: Entry) {
        // Для воспроизведения base64 TTS
        viewModelScope.launch {
            repository.reviewText(entry.text, entry.language)
                .onSuccess { result ->
                    result.ttsAudioUrl?.let { base64 ->
                        // Здесь используй MediaPlayer для base64
                        // Пример: playBase64Audio(base64)
                    }
                }
        }
    }
}

data class DiaryUiState(
    val isRecording: Boolean = false,
    val isLoading: Boolean = false,
    val selectedLanguage: String = "ru-RU",
    val entries: List<Entry> = emptyList(),
    val error: String? = null,
    val isBackendHealthy: Boolean = true
)