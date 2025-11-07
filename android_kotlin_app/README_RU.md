# Speaking Diary — Android (Kotlin, Jetpack Compose)

Это нативное Android‑приложение на Kotlin, повторяющее функциональность существующего Expo/React Native приложения.
Поддерживает запись аудио, распознавание речи, проверку фраз (review) и работу со списком записей при наличии токена.

## Что понадобится новичку
- Установить `Android Studio` (Arctic Fox или новее).
- JDK 17 (Android Studio обычно поставляет его автоматически).
- Android SDK (первый запуск предложит установить необходимые компоненты).

## Как запустить проект
1. Откройте папку `android_kotlin_app` как проект в Android Studio.
2. Дождитесь завершения Gradle Sync.
3. Установите/проверьте эмулятор (AVD) или подключите реальный Android‑устройство.
4. В файле `app/build.gradle.kts` по умолчанию задан `BuildConfig.BASE_URL`. Вы можете переопределить его в настройках приложения.
5. Запустите приложение кнопкой `Run` в Android Studio.

## Первичная настройка
- Откройте экран `Settings` внутри приложения.
- Укажите:
  - `Base URL` — адрес вашего бэкенда (например, `https://diary.pw-new.club`).
  - `Access Token` — токен для доступа к эндпоинтам, требующим авторизации (список записей, создание записи и т.п.).
  - `UI Language` — язык интерфейса для проверки фраз (например, `ru`).
- Нажмите `Сохранить`. После этого API‑клиент будет использовать указанный адрес и токен.

### Где взять токен
- Если используете Telegram WebApp аутентификацию — сервер умеет работать с JWT токеном.
- Можно получить токен через `/api/auth/telegram` (для WebApp) или, если он уже есть, активировать его через `/api/auth/select`.
- Мобильное приложение принимает токен в виде строки и передаёт его как `Authorization: Bearer <token>`.
- Если токен не указан, часть функций (список/создание записей) вернёт ошибку «Unauthorized». Распознавание (`/api/transcribe`) и проверка (`/api/review`) доступны без токена.

## Возможности приложения
- `Home` — список ваших записей (требуется токен). Кнопка `More details` открывает детальную проверку фразы.
- `Record` — запись аудио и отправка на распознавание (`/api/transcribe`). После распознавания текст можно проверить через `Review`.
- `Review` — проверка фразы на корректность (`/api/review`), получение исправленного варианта и пояснений.
- `Settings` — указание `Base URL`, `Access Token`, языка интерфейса.

## API соответствие (сервер)
- `GET /api/entries` — список записей текущего пользователя (требует токен).
- `POST /api/entries` — создание записи (требует токен).
- `GET /api/entries/{id}` — получить запись (требует токен).
- `PUT /api/entries/{id}` — обновить запись (требует токен).
- `DELETE /api/entries/{id}` — удалить запись (требует токен).
- `GET /api/search?q=...` — поиск по записям (требует токен).
- `POST /api/transcribe` — распознавание аудио (без токена). Форм‑данные: `audio` (файл), `language` (например, `auto`).
- `POST /api/review` — проверка текста. JSON: `{ text, language?, ui_language? }`.

## Права и разрешения
- Приложение запрашивает разрешение `RECORD_AUDIO` для записи звука.
- Для работы записи на Android 12+ убедитесь, что разрешения приложению выданы.

## Частые проблемы
- `Unauthorized` при запросах `/api/entries` — проверьте, что `Access Token` указан и действителен.
- Ошибка распознавания — проверьте размер и формат записываемого файла; по умолчанию используется `3gp` контейнер.
- Сетевая ошибка — убедитесь, что `Base URL` доступен со устройства/эмулятора и поддерживает HTTPS.

## Структура проекта
- `app/src/main/java/com/speakingdiary/` — код Kotlin (экраны, навигация, API‑клиент, настройки).
- `app/src/main/res/values*/` — строки интерфейса (`strings.xml`) и тема.
- `app/src/main/AndroidManifest.xml` — разрешения и главная activity.

## Сборка релиза
- В Android Studio откройте `Build > Generate Signed Bundle/APK`.
- Создайте подпись (keystore) и соберите `.apk` или `.aab`.
- Установите на устройство или загрузите в Play Console.

Если потребуется — я добавлю запись аудио через `MediaRecorder`/`AudioRecord`, воспроизведение через `ExoPlayer`, и полноценную детальную проверку записи по `id` с отображением пояснений и TTS.


============================================

Что я добавил

- android_kotlin_app/Dockerfile — образ с JDK17, Gradle, Android SDK, который собирает app-debug.apk .
- Сервис android_build в docker_compose.yml (профиль android ) — собирает APK и кладёт его в android_kotlin_app/app-debug.apk .
- android_kotlin_app/app/build.gradle.kts — добавил repositories { google(); mavenCentral() } .
- В манифесте включил usesCleartextTraffic=true , чтобы dev-бэкенд на http:// работал.
Как поднять локальные сервисы

- Бэкенд + фронтенд:
  - Создай .env из примера: Copy-Item .env.example .env
  - Запусти: docker compose -f docker_compose.yml up -d
  - Адреса:
    - Бэкенд: http://localhost:5000 ( /api/health )
    - Фронтенд: http://localhost:3000
- Если хочешь pgAdmin: docker compose -f docker_compose.yml --profile tools up -d pgadmin (на http://localhost:5050 ).
Собрать APK через Docker

- Требование: Docker Desktop должен работать в режиме Linux‑контейнеров.
  - Ошибка вида open //./pipe/dockerDesktopLinuxEngine говорит, что сейчас включены Windows‑контейнеры. Включи Linux‑контейнеры в Docker Desktop.
- Вариант 1 (Compose профиль):
  - Команда: docker compose -f docker_compose.yml --profile android up --build android_build
  - Результат: android_kotlin_app/app-debug.apk
- Вариант 2 (напрямую):
  - Собрать образ: docker build -t speaking-diary-android -f android_kotlin_app/Dockerfile android_kotlin_app
  - Запустить сборку: docker run --rm -v ${PWD}\\android_kotlin_app:/workspace speaking-diary-android
  - APK появится: android_kotlin_app\\app-debug.apk
Установка и запуск APK

- Эмулятор (Android Studio):
  - Открой Android Studio, запусти эмулятор, затем adb install -r android_kotlin_app\\app-debug.apk
  - Или просто нажми Run в Android Studio — он сам установит и запустит.
- Реальное устройство:
  - Включи «USB debugging», подключи, затем adb install -r android_kotlin_app\\app-debug.apk .
Настройка адресов

- На эмуляторе Base URL в Settings экрана ставь http://10.0.2.2:5000 (это localhost для эмулятора).
- На реальном устройстве — http://<IP_твоего_ПК>:5000 (убедись, что устройство видит ПК в сети).
- Для защищённого ( https ) хоста — можно сразу https://diary.pw-new.club .
Аутентификация

- Без токена доступны /api/transcribe и /api/review .
- Для /api/entries нужен Authorization: Bearer <token> . Токен укажи в Settings и сохрани.
Диагностика

- Ошибка Docker not found на compose без файла — используй явный флаг: -f docker_compose.yml .
- Предупреждение version is obsolete можно игнорировать или убрать строку version: '3.8' из compose.
- Если сборка падает на зависимостях — проверь сеть/прокси; мы добавили google() / mavenCentral() в проект.