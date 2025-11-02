# Voice Diary Android App (React Native / Expo)

Цель: создать нативное Android‑приложение с тем же UX/функционалом, что веб‑версия (`frontend`), работающее поверх существующего backend (`/api` на Flask/Caddy).

## Стек и язык
- Клиент: React Native + TypeScript (Expo managed workflow)
- Сборки/релизы: Expo EAS Build (Cloud) + Google Play Console
- Сеть: `axios`
- Навигация: `@react-navigation/native`
- Аудио: `expo-av`, `expo-file-system`
- Хранилище: `expo-secure-store` (токены), `@react-native-async-storage/async-storage` (настройки)
- i18n: `i18next` / `react-i18next` с переиспользованием JSON локалей из веба

## Архитектура
- `src/`
  - `screens/` — экраны (`Home`, `Record`, `Review`, `Settings`)
  - `components/` — UI-компоненты (Player, FlagBadge и т.п.)
  - `navigation/` — стек навигации
  - `api/` — клиент и сервисы (`entries`, `review`, `transcribe`, `translate`)
  - `i18n/` — настройка, локали
  - `store/` — состояние (язык интерфейса, текущая запись и т.д.)
  - `utils/` — вспомогательные утилиты

## Среда и конфигурация
- `API_BASE` — базовый URL API (по умолчанию `https://app.diary.pw-new.club/api`)
- `UI_LANGUAGE` — код языка интерфейса (например, `pl`, `ru`, `en`)
- Файл `.env` (создать из `.env.example`).

## Локальный запуск
1) Установить Node.js LTS и Expo CLI (`npm install -g expo-cli` — опционально).
2) В корне `android_app`: `npm install`.
3) Запуск:
   - `npm run start` — Metro bundler
   - `npm run android` — сборка/запуск на устройстве/эмуляторе
4) Проверить доступность API по `API_BASE`.

## Аудио‑поток
- Запись голоса в `Record` через `expo-av`.
- Загрузка аудио на сервер: `POST /api/transcribe` → получение текста.
- Создание записи: `POST /api/entries`.
- Ревью: `POST /api/review` с `ui_language` → показ `corrected_html`, `explanations_html`, `tts_audio_data_url`.

## i18n и локали
- Переиспользуем ключи из веба; локали можно импортировать как копии (`android_app/src/i18n/locales/*.json`).
- На сервер всегда отправляем `ui_language` текущего интерфейса.

## Docker / CI/CD
Хотя мобильные сборки не исполняются в Docker локально (Android SDK, образы и т.д.), Docker можно использовать для вспомогательных задач (линт/тесты/подготовка артефактов):

- Пример `Dockerfile.dev` (по желанию): Node + Yarn, установка зависимостей, запуск линтера/тестов.
- CI шаги:
  - Установка зависимостей
  - Линт/типизация (`npm run lint`, `tsc --noEmit`)
  - EAS Build (Cloud): генерирует `.aab` без локального Android SDK.

## EAS Build (Expo)
1) Установить EAS CLI: `npm install -g eas-cli`.
2) Войти: `eas login`.
3) Инициализация: `eas init`.
4) Конфигурация `eas.json` (создаётся автоматически; профили `preview`, `production`).
5) Кейстор:
   - `eas credentials` → создать/загрузить кейстор.
   - Сохранить секреты в безопасном месте.
6) Сборка:
   - `eas build -p android --profile production` → получаем `.aab`.

## Публикация в Google Play
1) Регистрация в Play Console (developer account).
2) Создать приложение: пакет (пример `pw.club.diary.app`), язык, страну, категорию.
3) Политики/безопасность: Privacy Policy URL (можно оформить в репозитории/сайте), Data Safety.
4) Подпись приложений: загрузить `.aab`, настроить подпись.
5) Контент: скриншоты, иконка, краткое/полное описание (локализация под основные языки).
6) Тест: внутренние/открытые тесты.
7) Релиз: Production, отслеживание крашей/ANR.

## Эндпоинты backend
- `GET /api/health` — проверка
- `GET /api/entries`, `POST /api/entries` — список/создание
- `GET /api/search?q=...` — поиск
- `POST /api/transcribe` — распознавание аудио
- `POST /api/review` — исправления и пояснения (с учётом `ui_language`)
- `POST /api/translate` — перевод для UI

## Безопасность
- Токен (JWT) хранить в `expo-secure-store`.
- Сетевые вызовы — только по HTTPS.
- Минимизировать персональные данные в логах.

## Структура (черновой каркас)
```
android_app/
  README.md
  package.json
  tsconfig.json
  babel.config.js
  app.json
  .env.example
  .gitignore
  src/
    App.tsx
    navigation/index.tsx
    screens/
      Home.tsx
      Record.tsx
      Review.tsx
      Settings.tsx
    api/
      client.ts
      review.ts
      entries.ts
      transcribe.ts
      translate.ts
    i18n/
      index.ts
      locales/
        en.json
        pl.json
        ru.json
```

## Дорожная карта
- F1: навигация, i18n, базовый UI
- F2: запись аудио, загрузка на сервер
- F3: экран ревью с диффом и пояснениями
- F4: стабильность, офлайн‑режим, аналитика
- F5: релиз, публикация и мониторинг

## Команды
- `npm run start` — запуск Metro
- `npm run android` — сборка/запуск на устройстве
- `npm run lint` — линт/типизация

Примечание: Expo/EAS избавляют от необходимости локально ставить Android SDK для сборки релизов — вместо этого используется облачная сборка.