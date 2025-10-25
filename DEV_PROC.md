# DEV_PROC — Шаг 1: Мобильное веб‑приложение дневника

Цель
- Создать минимальный, рабочий mobile‑first UI и API дневника без использования устаревших директорий.

Реализовано
- База данных: SQLite в `data/diary.sqlite`, таблица `entries (id, created_at, text)`.
- Инициализация: БД создаётся автоматически при старте приложения.
- API (FastAPI):
  - `GET /health` — проверка здоровья сервера.
  - `GET /` — главная страница (Jinja2 шаблон).
  - `GET /api/entries` — список последних записей (JSON).
  - `POST /api/entries` — создание записи из текста.
  - `POST /api/transcribe` — приём аудио (`form-data`) и возврат заглушки распознавания.
- UI (mobile‑first):
  - Главная страница с кнопкой «Создать запись».
  - Дерево записей, сгруппированных по датам (`YYYY-MM-DD`).
  - Модальное окно с микрофоном (MediaRecorder), кнопкой транскрибации и кнопкой «Сохранить».
- Файлы проекта:
  - `webapp/main.py` — сервер FastAPI, маршруты и инициализация БД.
  - `webapp/templates/index.html` — главная страница.
  - `webapp/static/app.js` — логика UI: запись аудио, транскрибация, сохранение, рендер дерева.
  - `webapp/static/styles.css` — мобильные стили.
  - `db/storage.py`, `db/__init__.py` — работа с SQLite: `init_db`, `add_entry`, `list_entries`, `get_entry`.
- Зависимости: добавлены `jinja2` (шаблоны) и `python-multipart` (form‑data для аудио).

Запуск и проверка
- Установить зависимости: `python -m pip install -r requirements.txt`
- Запустить дев‑сервер: `python -m uvicorn webapp.main:app --reload --port 8000`
- Открыть: `http://127.0.0.1:8000/` и проверить:
  - Создание записи через модальное окно.
  - Появление записи в дереве дат.
  - Отправку аудио и получение текстовой заглушки транскрибации.

# DEV_PROC — Шаг 2: Реальная транскрибация (Hugging Face)

Цель
- Подключить бесплатный внешний API для распознавания речи и получить реальный текст вместо заглушки.

Реализовано
- Эндпоинт `POST /api/transcribe` стал `async` и отправляет загруженный аудиофайл на Hugging Face Inference API (Whisper).
- Конфиг: читаются переменные окружения `HF_API_TOKEN` (а также `HUGGINGFACEHUB_API_TOKEN`, `HUGGINGFACE_API_TOKEN`) и опционально `HF_MODEL_URL` (по умолчанию `https://api-inference.huggingface.co/models/openai/whisper-base`).
- Надёжность: реализованы ретраи при `503 Model is loading` с короткой паузой.
- Файлы: аудио сохраняется в `data/uploads/<filename>`.
- Фронтенд: добавлена обработка ошибок в `app.js` (блокировка кнопки, вывод статуса и текста ошибки при сбое сети/серверного ответа).

Зависимости и конфиг
- Зависимости уже в проекте: `httpx`, `python-dotenv`.
- Переменные окружения (Windows PowerShell):
  - Установить токен на текущую сессию: ``$env:HF_API_TOKEN = "hf_XXXXXXXXXXXXXXXX"``
  - Установить навсегда: ``setx HF_API_TOKEN "hf_XXXXXXXXXXXXXXXX"`` (перезапустите терминал)
  - Опционально указать модель: ``$env:HF_MODEL_URL = "https://api-inference.huggingface.co/models/openai/whisper-small"``
- Можно создать `.env` в корне проекта:
  ```
  HF_API_TOKEN=hf_XXXXXXXXXXXXXXXX
  # HF_MODEL_URL=https://api-inference.huggingface.co/models/openai/whisper-small
  ```

Проверка
- UI: открыть `http://127.0.0.1:8000/`, записать → остановить → «Транскрибировать аудио». В поле текста появится результат распознавания.
- CLI: ``curl.exe -s -F "audio=@<путь_к_файлу>.webm" http://127.0.0.1:8000/api/transcribe`` → ожидается JSON `{"text":"..."}`.

Примечания
- Free tier Hugging Face может давать задержку из-за холодного старта (ответ 503); реализованы повторные попытки.
- При отсутствии токена возвращается безопасная заглушка, чтобы UI оставался рабочим.
- Следующим шагом можно добавить локальную транскрибацию (Vosk/faster-whisper) и переключение режима в конфиге.

Путь БД можно изменить через переменную окружения `DATABASE_URL` (по умолчанию `data/diary.sqlite`).
- Папка `.lagacy_diary` не используется.

# DEV_PROC — Шаг 3: Надёжность ASR и текущее использование

Цель
- Устранить ошибки 404/503 при транскрибации, добавить валидацию аудио и понятную конфигурацию. Подготовить офлайн‑режим.

Изменения в этом шаге
- Исправлен парсинг `DATABASE_URL` в `webapp/main.py`: поддержка `sqlite://`, `sqlite:///`, `file://` и обычных путей Windows. Устранён `WinError` для `sqlite:\data`.
- Эндпоинт `POST /api/transcribe` стал устойчивее:
  - Добавлена валидация формата (`.webm`, `.wav`, `.mp3`) и размера (по умолчанию 25 МБ, настраивается `MAX_AUDIO_SIZE_BYTES`).
  - Добавлен заголовок `x-wait-for-model: true` для ожидания прогрева модели на Hugging Face.
  - Реализован фолбэк моделей при `404`: сначала `HF_MODEL_URL`, затем `openai/whisper-small`, далее `openai/whisper-tiny`. При отсутствии токена или постоянных ошибках возвращается безопасная заглушка, чтобы UI оставался рабочим.
- Зависимости: добавлены пакеты для офлайн‑ASR и конвертации (`imageio-ffmpeg`, при необходимости `vosk`).

Как использовать приложение сейчас
- Настройте токен Hugging Face:
  - В текущей сессии PowerShell: `$env:HF_API_TOKEN = "hf_XXXXXXXXXXXXXXXX"`
  - Постоянно: `setx HF_API_TOKEN "hf_XXXXXXXXXXXXXXXX"` (перезапустите терминал)
- Опционально укажите более стабильную модель: `$env:HF_MODEL_URL = "https://api-inference.huggingface.co/models/openai/whisper-small"`
- Настройте лимит размера аудио (при необходимости): `setx MAX_AUDIO_SIZE_BYTES 26214400` (25 МБ)
- Запуск: `python -m uvicorn webapp.main:app --reload --port 8000` и откройте `http://127.0.0.1:8000/`.
- В UI: запишите аудио → «Транскрибировать аудио» → текст появится в поле ввода; сохраните запись.
- CLI‑проверка: `curl.exe -s -F "audio=@<путь_к_файлу>.webm" http://127.0.0.1:8000/api/transcribe` → ожидается `{"text":"..."}`.

Конфигурация БД
- `DATABASE_URL` может быть путём (`data/diary.sqlite`) или URI: `sqlite:///data/diary.sqlite`, `file://C:/.../data/diary.sqlite`.

Офлайн‑ASR (подготовка)
- В требования добавлены зависимости для локального распознавания (Vosk и конвертер аудио).
- Для работы Vosk потребуется модель и переменные окружения: `VOSK_MODEL_PATH` и `ASR_PROVIDER=vosk`.
- Скачайте модель с https://alphacephei.com/vosk/models, распакуйте, задайте `VOSK_MODEL_PATH`. Подключение офлайн‑режима будет оформлено отдельным шагом.

Примечания
- Ответ `503` от Hugging Face означает загрузку модели; реализованы повторные попытки.
- `GET /favicon.ico` может возвращать 404 — не влияет на функциональность.