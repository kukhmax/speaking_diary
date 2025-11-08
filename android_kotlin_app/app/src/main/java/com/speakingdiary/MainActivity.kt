package com.speakingdiary

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.ui.Modifier
import androidx.core.app.ActivityCompat
import com.speakingdiary.ui.screen.DiaryScreen
import com.speakingdiary.ui.theme.SpeakingDiaryTheme
import com.speakingdiary.utils.PermissionManager

class MainActivity : ComponentActivity() {
    private val permissionManager by lazy { PermissionManager(this) }

    private val permissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { isGranted ->
        if (!isGranted) {
            finish() // Закрыть приложение без разрешения
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // Запрос разрешения
        if (!permissionManager.checkRecordPermission()) {
            permissionLauncher.launch(android.Manifest.permission.RECORD_AUDIO)
        }

        setContent {
            SpeakingDiaryTheme {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background
                ) {
                    DiaryScreen()
                }
            }
        }
    }
}