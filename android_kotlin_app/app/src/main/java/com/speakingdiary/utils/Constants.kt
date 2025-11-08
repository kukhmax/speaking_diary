package com.speakingdiary.utils

object Constants {
    // Для эмулятора: 10.0.2.2 = localhost хоста
    const val BASE_URL = "http://10.0.2.2:5000"
    
    const val AUDIO_FILE_NAME = "recording.webm"
    const val AUDIO_MIME_TYPE = "audio/webm"
    
    val LANGUAGES = listOf(
        Language("ru-RU", "Русский"),
        Language("en-US", "English"),
        Language("pt-PT", "Português"),
        Language("es-ES", "Español"),
        Language("pl-PL", "Polski")
    )
}

data class Language(val code: String, val name: String)