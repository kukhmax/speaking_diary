package com.speakingdiary.data.api

import com.speakingdiary.data.model.Entry
import okhttp3.MultipartBody
import okhttp3.RequestBody
import retrofit2.Response
import retrofit2.http.*

data class TranscribeResponse(
    val text: String,
    val duration: Double
)

data class ReviewResponse(
    val original_text: String,
    val corrected_text: String,
    val explanations: String,
    val tts_audio_data_url: String?
)

interface ApiService {
    @Multipart
    @POST("/api/transcribe")
    suspend fun transcribeAudio(
        @Part audio: MultipartBody.Part,
        @Part("language") language: RequestBody
    ): Response<TranscribeResponse>

    @GET("/api/entries")
    suspend fun getEntries(): Response<List<Entry>>

    @POST("/api/entries")
    suspend fun createEntry(@Body entry: Entry): Response<Entry>

    @POST("/api/review")
    suspend fun reviewText(@Body request: Map<String, String>): Response<ReviewResponse>

    @GET("/api/health")
    suspend fun healthCheck(): Response<Map<String, String>>
}