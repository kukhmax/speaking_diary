package com.speakingdiary.network

import android.util.Log
import io.ktor.client.HttpClient
import io.ktor.client.call.body
import io.ktor.client.plugins.contentnegotiation.ContentNegotiation
import io.ktor.client.plugins.logging.LogLevel
import io.ktor.client.plugins.logging.Logger
import io.ktor.client.plugins.logging.Logging
import io.ktor.client.request.*
import io.ktor.http.ContentType
import io.ktor.http.HttpHeaders
import io.ktor.http.content.*
import io.ktor.serialization.kotlinx.json.json
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json
import com.speakingdiary.BuildConfig
import java.io.File

object ApiClient {
    private val json = Json { ignoreUnknownKeys = true }
    private val client = HttpClient {
        install(ContentNegotiation) { json(json) }
        install(Logging) {
            level = LogLevel.NONE
            logger = object : Logger { override fun log(message: String) { Log.d("ApiClient", message) } }
        }
    }

    private var token: String? = null
    private var baseUrl: String = BuildConfig.BASE_URL

    fun configure(baseUrlOverride: String?, accessToken: String?) {
        baseUrl = baseUrlOverride?.takeIf { it.isNotBlank() } ?: BuildConfig.BASE_URL
        token = accessToken?.takeIf { it.isNotBlank() }
    }

    private fun HttpRequestBuilder.applyAuth() {
        val t = token
        if (!t.isNullOrBlank()) {
            headers { append(HttpHeaders.Authorization, "Bearer $t") }
        }
    }

    // DTOs
    @Serializable
    data class EntryDto(
        val id: Int,
        val text: String,
        val language: String?,
        val timestamp: String?,
        val audio_duration: Double? = null
    )

    @Serializable
    data class EntriesResponse(
        val entries: List<EntryDto>,
        val total: Int,
        val page: Int,
        val per_page: Int,
        val pages: Int
    )

    @Serializable
    data class ReviewRequest(val text: String, val language: String? = null, val ui_language: String? = null)
    @Serializable
    data class ReviewResponse(
        val original_text: String,
        val corrected_text: String,
        val explanations: List<String> = emptyList(),
        val is_changed: Boolean = false,
        val language: String? = null,
        val tts_audio_data_url: String? = null
    )

    @Serializable
    data class CreateEntryRequest(val text: String, val language: String? = null, val audio_duration: Double? = null)

    @Serializable
    data class TranscribeResponse(val text: String, val language: String? = null)

    // API methods
    suspend fun getEntries(page: Int = 1, perPage: Int = 10, language: String? = null): EntriesResponse =
        client.get("$baseUrl/api/entries") {
            applyAuth()
            url {
                parameters.append("page", page.toString())
                parameters.append("per_page", perPage.toString())
                language?.let { parameters.append("language", it) }
            }
        }.body()

    suspend fun getEntry(id: Int): EntryDto = client.get("$baseUrl/api/entries/$id") { applyAuth() }.body()

    suspend fun createEntry(text: String, language: String? = null, audioDuration: Double? = null): EntryDto =
        client.post("$baseUrl/api/entries") {
            applyAuth()
            setBody(CreateEntryRequest(text, language, audioDuration))
        }.body()

    suspend fun updateEntry(id: Int, text: String? = null, language: String? = null, audioDuration: Double? = null): EntryDto =
        client.put("$baseUrl/api/entries/$id") {
            applyAuth()
            setBody(CreateEntryRequest(text ?: "", language, audioDuration))
        }.body()

    suspend fun review(text: String, language: String? = null, uiLanguage: String? = null): ReviewResponse =
        client.post("$baseUrl/api/review") {
            setBody(ReviewRequest(text, language, uiLanguage))
        }.body()

    suspend fun transcribeAudio(file: File, language: String = "auto"): TranscribeResponse =
        client.post("$baseUrl/api/transcribe") {
            setBody(MultiPartFormDataContent(formData {
                append("language", language)
                append("audio", file.readBytes(), Headers.build {
                    append(HttpHeaders.ContentType, ContentType.Application.OctetStream.toString())
                    append(HttpHeaders.ContentDisposition, "filename=\"${file.name}\"")
                })
            }))
        }.body()
}