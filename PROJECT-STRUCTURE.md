# 📁 Структура проекта "Дневник"

```
diary-app/
│
├── 📄 README.md                      # Главная документация
├── 📄 README-DOCKER.md               # Docker специфичная документация
├── 📄 DEPLOY.md                      # Руководство по деплою
├── 📄 QUICK-REFERENCE.md             # Шпаргалка команд
├── 📄 CHANGELOG.md                   # История изменений
├── 📄 PROJECT-STRUCTURE.md           # Этот файл
│
├── 🐳 docker-compose.yml             # Docker для разработки
├── 🐳 docker-compose.prod.yml        # Docker для продакшена
├── 📄 .env                           # Переменные окружения (не в Git!)
├── 📄 .env.example                   # Шаблон для .env
├── 📄 .gitignore                     # Исключения для Git
├── 📄 Makefile                       # Быстрые команды
│
├── 🔧 backend/                       # Backend (Python Flask)
│   ├── 📄 Dockerfile                 # Docker образ для backend
│   ├── 📄 .dockerignore              # Исключения Docker
│   ├── 🐍 app.py                     # Главный Flask сервер
│   ├── 📄 requirements.txt           # Python зависимости
│   ├── 📄 .env                       # Локальные переменные
│   ├── 🗄️ diary.db                   # SQLite база (только dev)
│   └── 📁 data/                      # Данные приложения
│
├── ⚛️ frontend/                      # Frontend (React)
│   ├── 📄 Dockerfile                 # Docker образ для frontend
│   ├── 📄 .dockerignore              # Исключения Docker
│   ├── 📄 nginx.conf                 # Конфигурация Nginx
│   ├── 📄 package.json               # Node зависимости
│   ├── 📄 package-lock.json          # Locked версии пакетов
│   ├── 📄 tailwind.config.js         # Конфигурация Tailwind
│   │
│   ├── 📁 public/                    # Статические файлы
│   │   ├── 📄 index.html
│   │   ├── 🖼️ favicon.ico
│   │   └── 📄 manifest.json
│   │
│   ├── 📁 src/                       # Исходный код React
│   │   ├── ⚛️ App.js                 # Главный компонент
│   │   ├── 🔧 api.js                 # API функции
│   │   ├── 🎨 index.css              # Tailwind стили
│   │   ├── 📄 index.js               # Точка входа
│   │   └── 📄 setupTests.js          # Настройка тестов
│   │
│   └── 📁 build/                     # Production build (генерируется)
│
├── 🌐 nginx/                         # Nginx конфигурация (продакшен)
│   ├── 📄 nginx.conf                 # Главная конфигурация
│   └── 🔐 ssl/                       # SSL сертификаты
│       └── 📁 live/
│           └── 📁 your-domain.com/
│               ├── 📄 fullchain.pem
│               └── 📄 privkey.pem
│
├── 💾 backups/                       # Резервные копии БД
│   ├── 📄 diary_backup_20251025.sql.gz
│   ├── 📄 diary_backup_20251024.sql.gz
│   └── ...
│
├── 📊 logs/                          # Логи (опционально)
│   ├── 📄 backend.log
│   ├── 📄 nginx.log
│   └── 📄 access.log
│
└── 🧪 .github/                       # GitHub Actions CI/CD
    └── 📁 workflows/
        └── 📄 deploy.yml             # Автоматический деплой
```

---

## 📝 Описание ключевых файлов

### 🔧 Backend файлы

#### `backend/app.py`
Главный Flask сервер с API endpoints:
- `/api/health` - health check
- `/api/transcribe` - транскрибация аудио через Groq
- `/api/entries` - CRUD операции с записями
- `/api/search` - поиск по тексту

**Технологии:**
- Flask 3.0
- SQLAlchemy (ORM)
- Groq API (Whisper)
- PostgreSQL/SQLite

#### `backend/requirements.txt`
```txt
Flask==3.0.0
Flask-CORS==4.0.0
Flask-SQLAlchemy==3.1.1
python-dotenv==1.0.0
groq==0.4.0
gunicorn==21.2.0
psycopg2-binary==2.9.9
```

#### `backend/Dockerfile`
Multi-stage Docker build:
1. Установка системных зависимостей
2. Установка Python пакетов
3. Копирование приложения
4. Настройка Gunicorn с 4 workers


---

### ⚛️ Frontend файлы

#### `frontend/src/App.js`
Главный React компонент (350+ строк):
- Запись аудио через MediaRecorder API
- Отображение записей в виде дерева
- Интеграция с backend API
- Responsive UI с Tailwind CSS

**Основные компоненты:**
- `DiaryApp` - главный компонент
- Modal окно записи
- Список записей с группировкой
- Аудио плеер

#### `frontend/src/api.js`
API клиент для взаимодействия с backend:
```javascript
- transcribeAudio(blob, language)
- getEntries()
- createEntry(entry)
- searchEntries(query)
```

#### `frontend/Dockerfile`
Multi-stage build:
1. **Stage 1 (build):** Node.js компиляция React
2. **Stage 2 (serve):** Nginx сервер (Alpine Linux)

Результат: образ ~50 MB (vs ~1 GB без multi-stage)

#### `frontend/nginx.conf`
Конфигурация для production:
- Gzip сжатие
- Security headers
- React Router support
- Кеширование статики (1 год)

---

### 🐳 Docker файлы

#### `docker-compose.yml` (Разработка)
```yaml
Сервисы:
- db (PostgreSQL)
- backend (Flask)
- frontend (React dev server)
- pgadmin (опционально)

Volumes:
- postgres_data
- backend_data

Networks:
- default (bridge)
```

#### `docker-compose.prod.yml` (Продакшен)
```yaml
Сервисы:
- db (PostgreSQL)
- backend (Flask + Gunicorn)
- frontend (React + Nginx)
- nginx (Reverse proxy)
- certbot (SSL)

Volumes:
- postgres_data_prod
- backend_data_prod
- certbot_data

Networks:
- internal (backend/db)
- web (frontend/nginx)
```

---

### 🌐 Nginx конфигурация

#### `nginx/nginx.conf` (Продакшен)
**Функции:**
- HTTP → HTTPS редирект
- Reverse proxy для backend API
- Кеширование статики
- Rate limiting (защита от DDoS)
- SSL/TLS конфигурация
- Security headers
- Gzip compression

**Endpoints:**
```
/           → frontend:80
/api/*      → backend:5000/api/*
/static/*   → frontend:80/static/* (cached)
```

---

### 📄 Документация

#### `README.md`
- Обзор проекта
- Пошаговая установка
- Настройка API ключей
- Локальная разработка
- FAQ

#### `README-DOCKER.md`
- Docker архитектура
- MediaRecorder vs Web Speech API
- Работа с контейнерами
- Troubleshooting
- Масштабирование

#### `DEPLOY.md`
- Выбор VPS провайдера
- Подготовка сервера
- Настройка домена и SSL
- CI/CD с GitHub Actions
- Мониторинг и backup

#### `QUICK-REFERENCE.md`
- Все команды в одном месте
- Docker shortcuts
- SQL запросы
- API endpoints
- Экстренные действия

#### `CHANGELOG.md`
- История версий
- Новые функции
- Исправления багов
- План будущих обновлений

---

## 🔄 Жизненный цикл файлов

### Разработка

```
1. Редактирование кода
   └─> frontend/src/App.js
   └─> backend/app.py

2. Тестирование локально
   └─> docker-compose up -d

3. Проверка в браузере
   └─> http://localhost:3000

4. Commit в Git
   └─> git commit -m "Update"

5. Push в GitHub
   └─> git push origin main
```

### Деплой

```
1. GitHub Actions запускается
   └─> .github/workflows/deploy.yml

2. Подключение к VPS
   └─> SSH в production сервер

3. Обновление кода
   └─> git pull origin main

4. Пересборка Docker
   └─> docker-compose -f docker-compose.prod.yml up -d --build

5. Health check
   └─> curl https://your-domain.com/api/health
```

---

## 📦 Размеры файлов

```
Исходный код:
├── backend/app.py           ~15 KB
├── frontend/src/App.js      ~12 KB
├── docker-compose.yml       ~2 KB
└── README.md                ~25 KB

Docker образы:
├── postgres:15-alpine       ~240 MB
├── backend (custom)         ~200 MB
├── frontend (custom)        ~50 MB
└── nginx:alpine             ~24 MB

Volumes (после использования):
├── postgres_data            ~50-500 MB
├── backend_data             ~1-10 MB
└── frontend/build           ~2 MB
```

---

## 🔐 Защищенные файлы (.gitignore)

```gitignore
# НЕ должны быть в Git:
.env                    # Секретные ключи
backend/.env
backend/diary.db        # Локальная БД
backend/__pycache__/
frontend/node_modules/
frontend/build/
nginx/ssl/              # SSL сертификаты
backups/                # Резервные копии
logs/                   # Логи
*.log
.DS_Store
```

---

## 🎯 Навигация по проекту

### Нужно изменить дизайн?
→ `frontend/src/App.js`
→ `frontend/src/index.css`
→ `frontend/tailwind.config.js`

### Нужно добавить API endpoint?
→ `backend/app.py` (добавить route)
→ `frontend/src/api.js` (добавить функцию)

### Нужно изменить настройки Docker?
→ `docker-compose.yml` (dev)
→ `docker-compose.prod.yml` (prod)

### Нужно настроить Nginx?
→ `nginx/nginx.conf` (reverse proxy)
→ `frontend/nginx.conf` (frontend serve)

### Нужно добавить документацию?
→ `README.md` (основное)
→ `DEPLOY.md` (деплой)
→ `QUICK-REFERENCE.md` (команды)

---

## 🚀 Быстрый старт по структуре

```bash
# 1. Клонировать проект
git clone your-repo.git
cd diary-app

# 2. Настроить переменные
cp .env.example .env
nano .env

# 3. Запустить
docker-compose up -d

# 4. Открыть
# Frontend: http://localhost:3000
# Backend:  http://localhost:5000
# pgAdmin:  http://localhost:5050
```

---

**Структура готова к разработке и продакшену! 🎉**