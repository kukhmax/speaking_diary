# 📔 Дневник - Голосовое приложение для заметок

> **v2.0** - Полноценное продакшн приложение с Docker, MediaRecorder API и Groq Whisper интеграцией

Мобильное веб-приложение для создания голосовых записей с автоматической транскрипцией на 5 языках.

---

## 🎯 Возможности

- ✅ **Запись голоса** с автоматической транскрибацией через Groq Whisper Large V3
- ✅ **MediaRecorder API** - запись, воспроизведение и сохранение аудио
- ✅ **5 языков**: русский, английский, португальский, испанский, польский
- ✅ **Docker контейнеризация** - запуск одной командой
- ✅ **PostgreSQL** - надежное хранение данных
- ✅ **Современный UI** - тёмная тема с градиентами в стиле pw-new.club
- ✅ **Продакшн ready** - SSL, мониторинг, backup'ы
- ✅ **100% бесплатно** - все сервисы имеют free tier

---

## 📚 Документация

| Документ | Описание |
|----------|----------|
| **[README.md](README.md)** | Вы здесь - основная информация |
| **[README-DOCKER.md](README-DOCKER.md)** | Docker и MediaRecorder детали |
| **[DEPLOY.md](DEPLOY.md)** | Деплой в продакшн на VPS |
| **[QUICK-REFERENCE.md](QUICK-REFERENCE.md)** | Шпаргалка команд |
| **[CHANGELOG.md](CHANGELOG.md)** | История изменений v1.0 → v2.0 |
| **[PROJECT-STRUCTURE.md](PROJECT-STRUCTURE.md)** | Структура проекта |

---

## 🚀 Быстрый старт

### Вариант 1: Docker (Рекомендуется)

```bash
# 1. Клонируйте проект
git clone https://github.com/your-username/diary-app.git
cd diary-app

# 2. Получите бесплатный Groq API ключ
# https://console.groq.com → API Keys → Create

# 3. Настройте .env
cp .env.example .env
nano .env  # Вставьте GROQ_API_KEY

# 4. Запустите (одна команда!)
docker-compose up -d

# 5. Откройте браузер
# http://localhost:3000
```

### Вариант 2: Makefile (Ещё проще)

```bash
make install  # Установка и настройка
make up       # Запуск
make logs     # Просмотр логов
```

---

## 🛠️ Технологии

### Frontend
- **React 18** - UI фреймворк
- **Tailwind CSS** - стилизация
- **MediaRecorder API** - запись аудио
- **Lucide Icons** - иконки

### Backend
- **Python 3.11** + **Flask** - REST API
- **SQLAlchemy** - ORM
- **PostgreSQL 15** - база данных
- **Groq API** - транскрибация (Whisper Large V3)

### DevOps
- **Docker + Docker Compose** - контейнеризация
- **Nginx** - reverse proxy
- **Let's Encrypt** - SSL сертификаты
- **GitHub Actions** - CI/CD

---

## 💰 Бесплатные сервисы

| Сервис | Назначение | Лимит (бесплатно) |
|--------|------------|-------------------|
| **[Groq](https://console.groq.com)** | Транскрибация | 14,400 req/день |
| **[Render.com](https://render.com)** | Backend хостинг | 750 часов/месяц |
| **[Vercel](https://vercel.com)** | Frontend хостинг | Безлимит |
| **[Supabase](https://supabase.com)** | PostgreSQL | 500 MB |
| **[Neon](https://neon.tech)** | PostgreSQL | 10 GB |
| **[Oracle Cloud](https://oracle.com/cloud/free)** | VPS сервер | 2 VM навсегда |
| **[Cloudflare](https://cloudflare.com)** | CDN + SSL | Безлимит |
| **[Uptime Robot](https://uptimerobot.com)** | Мониторинг | 50 мониторов |

---

## 📦 Структура проекта

```
diary-app/
├── 📄 docker-compose.yml          # Docker для разработки
├── 📄 docker-compose.prod.yml     # Docker для продакшена
├── 📄 .env                        # Переменные окружения
├── 📄 Makefile                    # Быстрые команды
│
├── backend/                       # Python Flask API
│   ├── app.py                     # REST API + Groq интеграция
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/                      # React приложение
│   ├── src/
│   │   ├── App.js                 # MediaRecorder + UI
│   │   └── api.js                 # API клиент
│   ├── Dockerfile
│   └── nginx.conf
│
├── nginx/                         # Nginx для продакшена
│   └── nginx.conf                 # Reverse proxy + SSL
│
└── 📚 docs/                       # Вся документация
    ├── README-DOCKER.md
    ├── DEPLOY.md
    └── QUICK-REFERENCE.md
```

Подробнее: **[PROJECT-STRUCTURE.md](PROJECT-STRUCTURE.md)**

---

## 🎨 Основные функции

### 1. Запись голоса (MediaRecorder)

```javascript
// Новое в v2.0:
- 🎤 Запись аудио через MediaRecorder API
- ⏱️ Таймер записи в реальном времени
- ▶️ Воспроизведение записанного аудио
- 🗑️ Удаление и перезапись
- 📊 Хранение длительности
```

### 2. Точная транскрибация (Groq Whisper)

```python
# Backend отправляет аудио на Groq API:
- 🎯 Точность 95%+ (vs 70% в браузере)
- 🌍 5 языков с отличным качеством
- ⚡ Скорость: 2-5 секунд
- 💰 Бесплатно: 14,400 запросов/день
```

### 3. Древовидная структура записей

```
📅 25 октября 2025 (3)
  ├── 14:30 - Встреча с клиентом... (0:45)
  ├── 12:15 - Идея для проекта... (1:20)
  └── 09:00 - Утренние мысли... (0:30)

📅 24 октября 2025 (5)
  └── ...
```

---

## 🆕 Новый функционал

### 1) Проверка и исправление текста (Gemini)
- Backend добавляет надёжный фолбэк на доступные модели: `gemini-1.5-pro(-latest)` → `gemini-1.5-flash(-latest)`.
- Если ни одна модель недоступна, вернётся исходный текст и пояснение.
- Требуется переменная окружения `GEMINI_API_KEY` (поддерживаются также `GOOGLE_API_KEY`/`GENAI_API_KEY`).

Как пользоваться:
- В UI: после сохранения записи backend автоматически вызывает `/api/review`. Откройте запись — появится модальное окно «Проверка и исправления» с исправленным текстом и пояснениями.
- Через API (Windows PowerShell):
  - `Invoke-RestMethod -Uri http://localhost:5000/api/review -Method Post -ContentType "application/json" -Body '{"text":"I want to teach English.","language":"en-US"}'`
- Через API (Linux/Mac):
  - `curl -s -X POST http://localhost:5000/api/review -H "Content-Type: application/json" -d '{"text":"I want to teach English.","language":"en-US"}'`

Ответ содержит поля: `original_text`, `corrected_text`, `corrected_html`, `explanations`, `explanations_html`, `is_changed`, `language`.

Технологии:
- `google-generativeai==0.8.5` (Gemini API)
- Flask (`/api/review`), JSON-парсинг с `request.get_json(silent=True)`

### 2) Флаги языков в UI (SVG)
- Эмодзи флаги заменены на SVG-иконки для стабильного отображения.
- Файлы: `frontend/public/flags/ru.svg`, `us.svg`, `pt.svg`, `es.svg`, `pl.svg`.
- В `frontend/src/App.js` массив языков теперь: `{ code, name, flagSrc }`, иконка отображается как `<img src={flagSrc} />`.

Как добавить новый язык:
- Положите SVG в `frontend/public/flags/<код>.svg`.
- Добавьте запись в массив `languages`:
  - `{ code: 'de-DE', name: 'Deutsch', flagSrc: '/flags/de.svg' }`

Технологии:
- React 18 + Tailwind CSS
- SVG-иконки в `public/flags`

### 3) Улучшения сборки и иконок
- `frontend/public/manifest.json`: удалены отсутствующие `logo192.png` и `logo512.png`, оставлен только `favicon.ico`.
- `frontend/public/index.html`: ссылка на иконку заменена на `favicon.ico`.

## 🔧 Установка и настройка

### Шаг 1: Установите Docker

**Windows/Mac:**
- Скачайте [Docker Desktop](https://www.docker.com/products/docker-desktop)

**Linux (Ubuntu/Debian):**
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER  # Перезайдите после этого
```

### Шаг 2: Получите Groq API ключ (бесплатно)

1. Зайдите на https://console.groq.com
2. Зарегистрируйтесь (GitHub/Google)
3. API Keys → Create API Key
4. Скопируйте ключ (начинается с `gsk_...`)

### Шаг 3: Настройте проект

```bash
# Клонируйте репозиторий
git clone https://github.com/your-username/diary-app.git
cd diary-app

# Создайте .env файл
cp .env.example .env

# Отредактируйте .env
nano .env
```

**Содержимое .env:**
```bash
# Groq API Key (обязательно!)
GROQ_API_KEY=gsk_ваш_ключ_здесь

# Database (будет создан автоматически)
DB_PASSWORD=измените_этот_пароль

# Flask Secret Key
SECRET_KEY=используйте_случайную_строку
```

### Шаг 4: Запустите приложение

```bash
# Вариант 1: Docker Compose
docker-compose up -d

# Вариант 2: Makefile
make up

# Проверьте статус
docker-compose ps

# Посмотрите логи
docker-compose logs -f
```

### Шаг 5: Откройте в браузере

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:5000
- **API Health:** http://localhost:5000/api/health
- **pgAdmin** (опционально): http://localhost:5050

---

## 📱 Использование

### Создание голосовой записи

1. Нажмите **"Создать запись"**
2. Выберите язык
3. Нажмите на микрофон 🎤
4. Говорите (идёт запись и таймер)
5. Нажмите ⏹️ (остановить)
6. Прослушайте ▶️ или удалите 🗑️
7. Дождитесь транскрибации
8. Отредактируйте текст при необходимости
9. Нажмите **"Сохранить"**

### Просмотр записей

- Записи автоматически группируются по датам
- Нажмите на дату чтобы развернуть/свернуть
- Показывается время и длительность каждой записи

---

## 🌍 Деплой в продакшн

Подробная инструкция: **[DEPLOY.md](DEPLOY.md)**

### Быстрый деплой на VPS

```bash
# На сервере (Ubuntu)
git clone https://github.com/your-username/diary-app.git
cd diary-app

# Настройте .env с продакшн настройками
nano .env

# Запустите с продакшн конфигурацией
docker-compose -f docker-compose.prod.yml up -d

# Настройте SSL (Let's Encrypt)
# См. DEPLOY.md - Шаг "Настройка SSL"
```

### Бесплатные VPS опции

- **Oracle Cloud Free Tier** - 2 VM навсегда (рекомендуется)
- **Google Cloud** - $300 кредитов на 90 дней
- **AWS Free Tier** - t2.micro на 12 месяцев

---

## 🔍 API Документация

### Эндпоинты

```http
GET    /api/health              # Health check
POST   /api/transcribe          # Транскрибация аудио
GET    /api/entries             # Получить все записи
POST   /api/entries             # Создать запись
GET    /api/entries/<id>        # Получить запись
PUT    /api/entries/<id>        # Обновить запись
DELETE /api/entries/<id>        # Удалить запись
GET    /api/search?q=<query>    # Поиск по тексту
```

### Примеры использования

```bash
# Health check
curl http://localhost:5000/api/health

# Транскрибация аудио
curl -X POST http://localhost:5000/api/transcribe \
  -F "audio=@recording.webm" \
  -F "language=ru-RU"

# Создать запись
curl -X POST http://localhost:5000/api/entries \
  -H "Content-Type: application/json" \
  -d '{"text":"Тестовая запись","language":"ru-RU"}'

# Поиск
curl "http://localhost:5000/api/search?q=встреча"
```

---

## 🛠️ Полезные команды

```bash
# Управление
make up           # Запустить
make down         # Остановить
make restart      # Перезапустить
make logs         # Показать логи
make rebuild      # Пересобрать

# База данных
make backup       # Создать backup
make restore      # Восстановить
make shell-db     # Подключиться к PostgreSQL

# Отладка
make check        # Проверить статус всех сервисов
make stats        # Показать использование ресурсов

# Очистка
make clean        # Мягкая очистка
make clean-all    # Полная очистка (удалит данные!)
```

Полный список: **[QUICK-REFERENCE.md](QUICK-REFERENCE.md)**

---

## 🔐 Безопасность

### Встроенная защита

- ✅ **Rate Limiting** - защита от DDoS
- ✅ **SSL/TLS** - автоматический HTTPS через Let's Encrypt
- ✅ **Security Headers** - HSTS, CSP, X-Frame-Options
- ✅ **Docker Isolation** - изолированные сети
- ✅ **Зашифрованные пароли** - хранение в .env

### Рекомендации для продакшена

1. Измените все пароли в `.env`
2. Используйте сильные случайные ключи
3. Включите Fail2ban на сервере
4. Настройте регулярные backup'ы
5. Используйте Cloudflare для дополнительной защиты

Подробнее: **[DEPLOY.md - Безопасность](DEPLOY.md#безопасность)**

---

## 🐛 Решение проблем

### Приложение не запускается

```bash
# Проверьте логи
docker-compose logs -f

# Проверьте что порты свободны
sudo lsof -i :3000
sudo lsof -i :5000
sudo lsof -i :5432

# Пересоздайте контейнеры
docker-compose down -v
docker-compose up -d --build
```

### Ошибка транскрибации

```bash
# Проверьте GROQ_API_KEY в .env
cat .env | grep GROQ

# Проверьте лимиты на console.groq.com

# Проверьте логи backend
docker-compose logs backend
```

### База данных не работает

```bash
# Проверьте статус
docker-compose ps

# Проверьте логи
docker-compose logs db

# Пересоздайте (ВНИМАНИЕ: удалит данные!)
docker-compose down -v
docker-compose up -d
```

Больше решений: **[README-DOCKER.md - Troubleshooting](README-DOCKER.md#возможные-проблемы-и-решения)**

---

## 📊 Что нового в v2.0

### Главные изменения

| Функция | v1.0 | v2.0 |
|---------|------|------|
| Транскрибация | Web Speech (браузер) | Groq Whisper API |
| Аудио | Не сохраняется | MediaRecorder + воспроизведение |
| Хранение | localStorage | PostgreSQL |
| Точность | 70-80% | 95%+ |
| Деплой | Вручную | Docker (1 команда) |
| SSL | Нет | Автоматический Let's Encrypt |
| Backup | Нет | Автоматический ежедневный |

Полная история: **[CHANGELOG.md](CHANGELOG.md)**

---

## 🔮 Планы на будущее (v3.0)

- [ ] Хранение аудио файлов (S3/MinIO)
- [ ] Теги и категории
- [ ] Экспорт в PDF/Word
- [ ] Аналитика и статистика
- [ ] Мультипользовательский режим
- [ ] AI саммаризация и анализ настроения
- [ ] Мобильные приложения (iOS/Android)

---

## 🤝 Вклад в проект

Приветствуем pull requests!

```bash
# 1. Fork проекта
# 2. Создайте ветку
git checkout -b feature/amazing-feature

# 3. Commit изменений
git commit -m 'Add amazing feature'

# 4. Push в ветку
git push origin feature/amazing-feature

# 5. Откройте Pull Request
```

---

## 📞 Поддержка

### Документация
- **[README-DOCKER.md](README-DOCKER.md)** - Docker детали
- **[DEPLOY.md](DEPLOY.md)** - Продакшн деплой
- **[QUICK-REFERENCE.md](QUICK-REFERENCE.md)** - Команды
- **[CHANGELOG.md](CHANGELOG.md)** - История версий

### Полезные ссылки
- **Groq Console:** https://console.groq.com
- **Docker Docs:** https://docs.docker.com
- **Flask Docs:** https://flask.palletsprojects.com
- **React Docs:** https://react.dev

### Помощь
1. Проверьте документацию выше
2. Посмотрите логи: `docker-compose logs -f`
3. Откройте issue на GitHub
4. Проверьте [Troubleshooting](README-DOCKER.md#возможные-проблемы-и-решения)

---

## 📄 Лицензия

MIT License - свободное использование

---

## 🙏 Благодарности

**Технологии:**
- React (Meta), Flask (Pallets), PostgreSQL
- Docker, Nginx, Tailwind CSS

**Сервисы:**
- Groq (бесплатная транскрибация)
- Let's Encrypt (бесплатный SSL)

---

<div align="center">

**Дневник v2.0** - Готов к использованию! 🚀

[Документация](README-DOCKER.md) • [Деплой](DEPLOY.md) • [Команды](QUICK-REFERENCE.md) • [GitHub](https://github.com/your-username/diary-app)

</div># 📔 Дневник - Голосовое приложение для заметок

Мобильное веб-приложение для создания голосовых записей с автоматической транскрипцией на 5 языках.

## 🎯 Возможности

- ✅ Запись голоса с автоматической транскрибацией
- ✅ Поддержка 5 языков: русский, английский, португальский, испанский, польский
- ✅ Древовидное отображение записей по датам
- ✅ Редактирование текста вручную
- ✅ Поиск по записям
- ✅ Современный дизайн в стиле pw-new.club
- ✅ Адаптивный интерфейс для мобильных устройств

## 🚀 Технологии

### Frontend
- React 18
- Tailwind CSS
- Web Speech API (встроенная транскрипция браузера)
- Lucide Icons

### Backend
- Python 3.9+
- Flask
- SQLAlchemy (SQLite/PostgreSQL)
- Groq API (бесплатная транскрибация Whisper)

## 💰 Бесплатные API и сервисы

### 1. Groq API (РЕКОМЕНДУЕТСЯ - 100% бесплатно)
- **Модель:** Whisper Large V3
- **Лимиты:** 14,400 запросов в день (бесплатно)
- **Качество:** Отличное для всех 5 языков
- **Регистрация:** https://console.groq.com

### 2. AssemblyAI (Альтернатива - пробный период)
- **Бесплатно:** 5 часов транскрибации в месяц
- **Регистрация:** https://www.assemblyai.com

### 3. Deepgram (Альтернатива - пробный период)
- **Бесплатно:** $200 кредитов (~45 часов аудио)
- **Регистрация:** https://deepgram.com

## 📦 Установка

### Предварительные требования

```bash
# Установите Python 3.9+ (проверьте версию)
python --version

# Установите Node.js 18+ (проверьте версию)
node --version
npm --version

# Установите Git
git --version
```

### Шаг 1: Клонирование репозитория

```bash
# Создайте директорию для проекта
mkdir diary-app
cd diary-app

# Создайте структуру проекта
mkdir backend frontend
```

### Шаг 2: Настройка Backend

```bash
cd backend

# Создайте виртуальное окружение Python
python -m venv venv

# Активируйте виртуальное окружение
# На Windows:
venv\Scripts\activate
# На macOS/Linux:
source venv/bin/activate

# Установите зависимости
pip install -r requirements.txt
```

**Создайте файлы:**

1. Скопируйте `app.py` в `backend/app.py`
2. Скопируйте `requirements.txt` в `backend/requirements.txt`
3. Скопируйте `.env.example` в `backend/.env`

### Шаг 3: Получение Groq API Key (БЕСПЛАТНО)

1. Перейдите на https://console.groq.com
2. Зарегистрируйтесь (можно через Google/GitHub)
3. Перейдите в раздел API Keys
4. Создайте новый API Key
5. Скопируйте ключ в файл `.env`:

```bash
GROQ_API_KEY=gsk_ваш_ключ_здесь
```

### Шаг 4: Запуск Backend

```bash
# Убедитесь что вы в директории backend и venv активирован
python app.py

# Сервер запустится на http://localhost:5000
# Проверьте: http://localhost:5000/api/health
```

### Шаг 5: Настройка Frontend

```bash
# Откройте новый терминал и перейдите в директорию frontend
cd frontend

# Инициализируйте React проект
npx create-react-app .

# Установите дополнительные зависимости
npm install lucide-react axios
```

**Обновите файлы:**

1. Замените содержимое `src/App.js` на код React компонента из артефакта
2. Настройте Tailwind CSS (см. ниже)

### Шаг 6: Настройка Tailwind CSS

```bash
# Установите Tailwind
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

**Обновите `tailwind.config.js`:**

```javascript
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
```

**Обновите `src/index.css`:**

```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

### Шаг 7: Интеграция Backend с Frontend

Создайте `src/api.js`:

```javascript
import axios from 'axios';

const API_BASE_URL = 'http://localhost:5000/api';

export const transcribeAudio = async (audioBlob, language) => {
  const formData = new FormData();
  formData.append('audio', audioBlob, 'recording.webm');
  formData.append('language', language);

  const response = await axios.post(`${API_BASE_URL}/transcribe`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });

  return response.data;
};

export const getEntries = async () => {
  const response = await axios.get(`${API_BASE_URL}/entries`);
  return response.data;
};

export const createEntry = async (entry) => {
  const response = await axios.post(`${API_BASE_URL}/entries`, entry);
  return response.data;
};

export const searchEntries = async (query) => {
  const response = await axios.get(`${API_BASE_URL}/search?q=${query}`);
  return response.data;
};
```

### Шаг 8: Запуск Frontend

```bash
# В директории frontend
npm start

# Приложение откроется на http://localhost:3000
```

## 🗄️ Настройка PostgreSQL (опционально, для продакшена)

### На локальной машине:

```bash
# Установите PostgreSQL
# Windows: https://www.postgresql.org/download/windows/
# macOS: brew install postgresql
# Linux: sudo apt install postgresql

# Создайте базу данных
psql -U postgres
CREATE DATABASE diary_db;
CREATE USER diary_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE diary_db TO diary_user;
\q

# Обновите .env
DATABASE_URL=postgresql://diary_user:your_password@localhost:5432/diary_db
```

### Бесплатные хостинги для PostgreSQL:

1. **Supabase** - https://supabase.com
   - 500 MB бесплатно
   - Бесплатные backups

2. **Neon** - https://neon.tech
   - 10 GB бесплатно
   - Serverless PostgreSQL

3. **ElephantSQL** - https://www.elephantsql.com
   - 20 MB бесплатно
   - Отлично для тестирования

## 🚀 Деплой (бесплатные варианты)

### Backend (выберите один)

#### 1. Render.com (РЕКОМЕНДУЕТСЯ)
- **Сайт:** https://render.com
- **Лимиты:** 750 часов в месяц бесплатно
- **Шаги:**
  1. Создайте аккаунт
  2. New → Web Service
  3. Подключите Git репозиторий
  4. Build Command: `pip install -r requirements.txt`
  5. Start Command: `gunicorn app:app`
  6. Добавьте переменные окружения (GROQ_API_KEY)

#### 2. Railway.app
- **Сайт:** https://railway.app
- **Лимиты:** $5 кредитов в месяц бесплатно
- Аналогичные шаги

#### 3. Fly.io
- **Сайт:** https://fly.io
- **Лимиты:** 3 VM бесплатно

### Frontend (выберите один)

#### 1. Vercel (РЕКОМЕНДУЕТСЯ для React)
- **Сайт:** https://vercel.com
- **Лимиты:** Безлимитный бесплатный план
- **Шаги:**
  1. Создайте аккаунт
  2. Import Project
  3. Подключите Git репозиторий
  4. Авто-деплой!

#### 2. Netlify
- **Сайт:** https://netlify.com
- **Лимиты:** 100 GB bandwidth бесплатно

#### 3. GitHub Pages
- Бесплатно, но только для статических сайтов

## 📱 Структура проекта

```
diary-app/
├── backend/
│   ├── app.py              # Основной Flask сервер
│   ├── requirements.txt    # Python зависимости
│   ├── .env               # Переменные окружения
│   └── diary.db           # SQLite база данных (создастся автоматически)
│
└── frontend/
    ├── public/
    ├── src/
    │   ├── App.js         # Основной React компонент
    │   ├── api.js         # API функции
    │   ├── index.css      # Tailwind стили
    │   └── index.js       # Точка входа
    ├── package.json
    └── tailwind.config.js
```

## 🧪 Тестирование API

Используйте curl или Postman:

```bash
# Health check
curl http://localhost:5000/api/health

# Получить все записи
curl http://localhost:5000/api/entries

# Создать запись
curl -X POST http://localhost:5000/api/entries \
  -H "Content-Type: application/json" \
  -d '{"text": "Тестовая запись", "language": "ru-RU"}'

# Поиск
curl "http://localhost:5000/api/search?q=тест"
```

## 🔧 Возможные проблемы и решения

### 1. Ошибка CORS
```bash
# Убедитесь что Flask-CORS установлен
pip install Flask-CORS
```

### 2. Ошибка микрофона в браузере
- Используйте HTTPS или localhost
- Разрешите доступ к микрофону в настройках браузера

### 3. Ошибка Groq API
```bash
# Проверьте что ключ правильно прописан в .env
# Проверьте лимиты на https://console.groq.com
```

### 4. Ошибка базы данных
```bash
# Пересоздайте базу
rm diary.db
python app.py  # База создастся автоматически
```

## 📊 Лимиты бесплатных сервисов

| Сервис | Бесплатный лимит | Период |
|--------|------------------|--------|
| Groq API | 14,400 запросов | День |
| Render.com | 750 часов | Месяц |
| Vercel | Безлимит | - |
| Supabase | 500 MB | Всегда |
| Neon | 10 GB | Всегда |

## 🎨 Кастомизация

### Изменить цветовую схему

В React компоненте найдите градиенты:
```javascript
// Замените purple/pink на другие цвета Tailwind
from-purple-600 to-pink-600  // Основной градиент
from-slate-900 via-purple-900 // Фон
```

### Добавить новые языки

1. В React компоненте добавьте язык в массив `languages`
2. В Backend добавьте маппинг в `lang_map`

## 📚 Дополнительные ресурсы

- **Groq Documentation:** https://console.groq.com/docs
- **Flask Tutorial:** https://flask.palletsprojects.com
- **React Documentation:** https://react.dev
- **Tailwind CSS:** https://tailwindcss.com/docs

## 🤝 Поддержка

Если возникли вопросы:
1. Проверьте логи в терминале
2. Убедитесь что все API ключи правильно настроены
3. Проверьте что все сервисы запущены (backend + frontend)

## 📝 Лицензия

MIT License - свободное использование

---

**Приятного использования! 🎉**