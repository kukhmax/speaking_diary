package com.speakingdiary.ui.components

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import com.speakingdiary.utils.Constants

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun LanguageSelector(
    selectedLanguage: String,
    onLanguageSelected: (String) -> Unit
) {
    SingleChoiceSegmentedButtonRow(
        modifier = Modifier.fillMaxWidth().padding(horizontal = 16.dp)
    ) {
        Constants.LANGUAGES.forEachIndexed { index, language ->
            SegmentedButton(
                selected = selectedLanguage == language.code,
                onClick = { onLanguageSelected(language.code) },
                shape = SegmentedButtonDefaults.itemShape(
                    index = index,
                    count = Constants.LANGUAGES.size
                ),
                colors = SegmentedButtonDefaults.colors(
                    activeContainerColor = Color(0xFF7C3AED),
                    activeContentColor = Color.White,
                    inactiveContainerColor = Color(0xFF1E293B),
                    inactiveContentColor = Color.Gray
                )
            ) {
                Text(language.name, style = MaterialTheme.typography.labelMedium)
            }
        }
    }
}