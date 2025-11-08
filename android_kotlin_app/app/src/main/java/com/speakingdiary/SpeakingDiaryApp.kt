package com.speakingdiary

import android.app.Application

class SpeakingDiaryApp : Application() {
    companion object {
        lateinit var instance: SpeakingDiaryApp
            private set
    }

    override fun onCreate() {
        super.onCreate()
        instance = this
    }
}