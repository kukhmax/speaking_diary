package com.speakingdiary

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.runtime.Composable
import androidx.compose.ui.tooling.preview.Preview
import androidx.navigation.NavHostController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.speakingdiary.ui.screens.HomeScreen
import com.speakingdiary.ui.screens.RecordScreen
import com.speakingdiary.ui.screens.ReviewScreen
import com.speakingdiary.ui.screens.SettingsScreen
import com.speakingdiary.pref.Prefs
import com.speakingdiary.network.ApiClient

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        // Configure API with stored settings
        ApiClient.configure(Prefs.getBaseUrl(this), Prefs.getToken(this))
        setContent {
            MaterialTheme {
                Surface(color = MaterialTheme.colorScheme.background) {
                    AppNavHost()
                }
            }
        }
    }
}

@Composable
fun AppNavHost(navController: NavHostController = rememberNavController()) {
    NavHost(navController = navController, startDestination = "home") {
        composable("home") {
            HomeScreen(
                onOpenDetails = { id -> navController.navigate("review/$id") },
                onGoRecord = { navController.navigate("record") },
                onGoSettings = { navController.navigate("settings") }
            )
        }
        composable("record") { RecordScreen(onBack = { navController.popBackStack() }) }
        composable("review/{id}") { ReviewScreen(onBack = { navController.popBackStack() }) }
        composable("settings") { SettingsScreen(onBack = { navController.popBackStack() }) }
    }
}

@Preview(showBackground = true)
@Composable
fun AppPreview() {
    MaterialTheme {
        AppNavHost()
    }
}