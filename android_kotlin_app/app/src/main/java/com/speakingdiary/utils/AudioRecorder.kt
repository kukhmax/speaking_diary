package com.speakingdiary.utils

import android.media.MediaRecorder
import java.io.File

class AudioRecorder(private val outputFile: File) {
    private var recorder: MediaRecorder? = null
    var isRecording = false
        private set

    fun start(): Result<Unit> = runCatching {
        recorder = MediaRecorder().apply {
            setAudioSource(MediaRecorder.AudioSource.MIC)
            setOutputFormat(MediaRecorder.OutputFormat.WEBM)
            setAudioEncoder(MediaRecorder.AudioEncoder.AAC)
            setAudioEncodingBitRate(128000)
            setAudioSamplingRate(44100)
            setOutputFile(outputFile.absolutePath)
            prepare()
            start()
        }
        isRecording = true
    }

    fun stop(): Result<File> = runCatching {
        recorder?.apply {
            stop()
            release()
        }
        recorder = null
        isRecording = false
        outputFile
    }
}