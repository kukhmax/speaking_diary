# Speaking Diary Android — Полная инструкция установки

## 📋 Требования

- **Android Studio Hedgehog 2023.1.1+**
- **JDK 17** (установленный и настроенный в Android Studio)
- **Android SDK API 26+** (Android 8.0+)
- **Эмулятор или физическое устройство с Android 8.0+**
- **Flask Backend** (запущенный на `localhost:5000`)

---

## 🚀 Быстрый старт (15 минут)

### Шаг 1: Клонировать и создать проект

1. Открой Android Studio → **File → New → New Project**
2. Выбери **Empty Activity (Compose)**
3. Настрой параметры:
   - **Name**: `Speaking Diary`
   - **Package name**: `com.speakingdiary`
   - **Save location**: `~/projects/speaking-diary-android`
   - **Minimum SDK**: **API 26: Android 8.0**
   - **Build Configuration Language**: **Kotlin**

4. Дождись создания и синхронизации Gradle

---

### Шаг 2: Заменить файлы

**Удали автоматически созданные файлы:**
- `app/src/main/java/com/speakingdiary/MainActivity.kt`
- `app/src/main/java/com/speakingdiary/ui/theme/*` (весь пакет)

**Скопируй мои файлы** в соответствующие директории:

```
app/src/main/java/com/speakingdiary/
├── MainActivity.kt
├── SpeakingDiaryApp.kt
├── data/
│   ├── api/ApiService.kt
│   ├── model/Entry.kt
│   └── repository/DiaryRepository.kt
├── ui/
│   ├── screen/DiaryScreen.kt
│   ├── components/
│   │   ├── EntryItem.kt
│   │   └── LanguageSelector.kt
│   └── viewmodel/DiaryViewModel.kt
└── utils/
├── AudioRecorder.kt
├── Constants.kt
└── PermissionManager.kt
```

**Ресурсы:**
```
app/src/main/res/
├── drawable/ic_mic.xml
├── xml/network_security_config.xml
└── values/
├── strings.xml
├── colors.xml
└── themes.xml
```

**Корневые файлы:**
```
├── build.gradle.kts (корневой)
├── settings.gradle.kts
└── app/build.gradle.kts
```

---

### Шаг 3: Синхронизировать Gradle

1. Открой `app/build.gradle.kts`
2. Android Studio предложит **"Sync Now"** — нажми
3. Если есть ошибки, нажми **File → Sync Project with Gradle Files**

---

### Шаг 4: Настроить Backend

Убедись, что Flask backend запущен:

```bash
# В директории speaking_diary (Python проект)
docker-compose up -d

# Проверь health endpoint
curl http://localhost:5000/api/health
# Должно вернуть: {"status": "ok"}
```


### Шаг 5: Настроить эмулятор

1. Открой Tools → Device Manager
2. Создай новый эмулятор:
    - Device: Pixel 7/8
    - System Image: API 34 (Android 14) Google Play
    - Graphics: Hardware - GLES 2.0
3. Запусти эмулятор

### Шаг 6: Запустить приложение

1. Выбери эмулятор в списке устройств (панель сверху)
2. Нажми Shift + F10 (или зелёную стрелку ▶️)
3. Дождись установки APK

### 🔧 Настройка для продакшена

Проброс backend на реальном устройстве

Если тестируешь на физическом устройстве (не эмулятор), замени BASE_URL:

```kotlin
// в app/src/main/java/com/speakingdiary/utils/Constants.kt
object Constants {
    // Пример: твой компьютер в локальной сети
    const val BASE_URL = "http://192.168.1.100:5000"
}
```

Как узнать IP хоста:
```bash
# Linux/macOS
ifconfig | grep "inet " | grep -v 127.0.0.1

# Windows
ipconfig
```

#### 🐛 Решение проблем

Ошибка: "Cleartext HTTP traffic not permitted"

Причина: Android 9+ блокирует HTTP

Решение: Уже настроено в network_security_config.xml, но для продакшена добавь:
```xml
<!-- app/src/main/res/xml/network_security_config.xml -->
<domain includeSubdomains="true">your-domain.com</domain>
```

#### Ошибка: "Unable to connect to localhost:5000"

Причина: Эмулятор не видит localhost хоста

Решение: Используй 10.0.2.2 (уже настроено)

#### Ошибка: "Permission denied for audio recording"

Причина: Пользователь отклонил разрешение

Решение: Закрой и открой приложение снова

#### Ошибка: "CORS policy blocked"

Причина: Flask не принимает запросы с Android

Решение: В Python backend добавь:
```Python
# backend/app.py
from flask_cors import CORS
CORS(app, resources={r"/api/*": {"origins": "*"}})
```

#### ✅ Проверка функционала

1. Запись: Нажми FAB (микрофон) → говори → нажми стоп
2. Транскрибация: Должна появиться через 2-5 сек
3. Список: Запись появится в древовидном списке
4. Озвучивание: Нажми ▶️ на записи, услышишь исправленную версию
5. Оффлайн: Room автоматически кэширует записи

#### 📊 Тестирование

Unit тесты (опционально)
Создай app/src/test/java/com/speakingdiary/DiaryViewModelTest.kt:
```kotlin
class DiaryViewModelTest {
    @Test
    fun `should toggle recording state`() {
        // Mock repository and test
    }
}
```

Запуск: ``` ./gradlew test```

#### UI тесты
Создай app/src/androidTest/java/com/speakingdiary/DiaryScreenTest.kt:
```kotlin
@get:Rule
val composeTestRule = createComposeRule()

@Test
fun recordButton_togglesIcon() {
    composeTestRule.setContent { DiaryScreen() }
    composeTestRule.onNodeWithTag("record_fab").performClick()
    composeTestRule.onNodeWithContentDescription("Stop").assertExists()
}
```

Запуск: ``` ./gradlew connectedAndroidTest```

#### 🎯 Переход на продакшн

Деплой backend

1. VPS (Oracle Cloud Free Tier):
```bash
# На сервере
git clone https://github.com/kukhmax/speaking_diary.git
cd speaking_diary
nano .env  # Вставь KEYS
docker-compose -f docker-compose.prod.yml up -d
```

2. SSL:
```bash
# В папке nginx/
certbot --nginx -d your-domain.com
```

3. Обнови BASE_URL в Constants.kt:
```kotlin
// в app/src/main/java/com/speakingdiary/utils/Constants.kt
object Constants {
    // Пример: твой компьютер в локальной сети
    const val BASE_URL = "https://your-domain.com"
}
```
#### 📚 Полезные команды

```bash
# Очистка и пересборка
./gradlew clean build

# Запуск на эмуляторе
./gradlew installDebug

# Просмотр логов
adb logcat | grep "SpeakingDiary"

# Создание APK
./gradlew assembleRelease
# APK: app/build/outputs/apk/release/
```