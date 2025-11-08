package com.speakingdiary.data.repository

import com.speakingdiary.data.api.ApiService
import com.speakingdiary.data.model.Entry
import com.speakingdiary.utils.Constants
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.MultipartBody
import okhttp3.RequestBody.Companion.asRequestBody
import okhttp3.RequestBody.Companion.toRequestBody
import java.io.File

class DiaryRepository(private val api: ApiService) {
    suspend fun transcribeAudio(audioFile: File, language: String): Result<String> = runCatching {
        val requestFile = audioFile.asRequestBody(Constants.AUDIO_MIME_TYPE.toMediaType())
        val audioPart = MultipartBody.Part.createFormData("audio", audioFile.name, requestFile)
        val languagePart = language.toRequestBody("text/plain".toMediaType())

        val response = api.transcribeAudio(audioPart, languagePart)
        if (!response.isSuccessful) throw Exception("Transcription failed: ${response.code()}")
        response.body()?.text ?: throw Exception("Empty response")
    }

    suspend fun createEntry(text: String, language: String, duration: Double): Result<Entry> = runCatching {
        val entry = Entry(text = text, language = language, duration = duration)
        val response = api.createEntry(entry)
        if (!response.isSuccessful) throw Exception("Failed to save: ${response.code()}")
        response.body() ?: throw Exception("Empty response")
    }

    suspend fun getEntries(): Result<List<Entry>> = runCatching {
        val response = api.getEntries()
        if (!response.isSuccessful) throw Exception("Failed to load: ${response.code()}")
        response.body() ?: emptyList()
    }

    suspend fun reviewText(text: String, language: String): Result<ReviewResult> = runCatching {
        val request = mapOf("text" to text, "language" to language)
        val response = api.reviewText(request)
        if (!response.isSuccessful) throw Exception("Review failed: ${response.code()}")
        val body = response.body() ?: throw Exception("Empty response")
        ReviewResult(
            correctedText = body.corrected_text,
            explanations = body.explanations,
            ttsAudioUrl = body.tts_audio_data_url
        )
    }

    suspend fun healthCheck(): Result<Boolean> = runCatching {
        val response = api.healthCheck()
        response.isSuccessful
    }
}

data class ReviewResult(
    val correctedText: String,
    val explanations: String,
    val ttsAudioUrl: String?
)