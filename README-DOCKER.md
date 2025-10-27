# 🐳 Docker Инструкция для Дневника

## 📋 Что изменилось

### ✨ Новые возможности:

1. **MediaRecorder API** вместо Web Speech API:
   - ✅ Запись аудио файлов (можно прослушать)
   - ✅ Отправка на backend для точной транскрибации
   - ✅ Хранение длительности записи
   - ✅ Кнопки воспроизведения и удаления аудио
   - ✅ Таймер записи
   - ✅ Лучшее качество распознавания через Groq Whisper

2. **Docker контейнеризация**:
   - ✅ Один клик для запуска всего стека
   - ✅ PostgreSQL база данных
   - ✅ Backend API (Flask)
   - ✅ Frontend (React + Nginx)
   - ✅ pgAdmin для управления БД (опционально)

## 🚀 Быстрый старт с Docker

### Предварительные требования

Установите Docker и Docker Compose:

**Windows:**
- Скачайте [Docker Desktop](https://www.docker.com/products/docker-desktop)

**macOS:**
```bash
brew install docker docker-compose
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install docker.io docker-compose
sudo systemctl start docker
sudo usermod -aG docker $USER  # перезайдите в систему после этого
```

Проверьте установку:
```bash
docker --version
docker-compose --version
```

### Шаг 1: Подготовка проекта

```bash
# Создайте структуру проекта
mkdir diary-app
cd diary-app

# Создайте директории
mkdir -p backend frontend
```

### Шаг 2: Добавьте файлы

Скопируйте следующие файлы в проект:

```
diary-app/
├── docker-compose.yml          # Главный файл конфигурации
├── .env                        # Переменные окружения
├── backend/
│   ├── Dockerfile
│   ├── app.py
│   ├── requirements.txt
│   └── .dockerignore
└── frontend/
    ├── Dockerfile
    ├── nginx.conf
    ├── package.json
    ├── src/
    │   ├── App.js
    │   └── ...
    └── .dockerignore
```

**Создайте `.dockerignore` в backend:**
```
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
venv/
*.db
.env
.git/
.gitignore
```

**Создайте `.dockerignore` в frontend:**
```
node_modules/
build/
.git/
.gitignore
*.log
npm-debug.log*
.DS_Store
.env.local
.env.development.local
.env.test.local
.env.production.local
```

### Шаг 3: Настройка переменных окружения

Создайте файл `.env` в корне проекта:

```bash
# Database
DB_PASSWORD=your_secure_password_123

# Groq API Key (получите бесплатно на https://console.groq.com)
GROQ_API_KEY=gsk_your_api_key_here

# Flask
SECRET_KEY=your_super_secret_key_for_production

# pgAdmin (опционально)
PGADMIN_PASSWORD=admin_password_123

# Frontend API URL
REACT_APP_API_URL=http://localhost:5000/api

# ===== TTS (optional) =====
# Edge TTS voice overrides (опционально)
# EDGE_TTS_VOICE=
# EDGE_TTS_PT_VOICE=

# Разрешить фоллбэк на gTTS для португальского (pt-PT)
# ВНИМАНИЕ: gTTS 'pt' использует бразильский акцент
ALLOW_PT_GTTs_FALLBACK=false
```

### Шаг 4: Получение Groq API Key

1. Зайдите на https://console.groq.com
2. Зарегистрируйтесь (бесплатно)
3. Создайте API Key в разделе "API Keys"
4. Скопируйте ключ в `.env` файл

### Шаг 5: Запуск приложения

```bash
# Запуск всех сервисов
docker-compose up -d

# Проверка статуса
docker-compose ps

# Просмотр логов
docker-compose logs -f

# Просмотр логов конкретного сервиса
docker-compose logs -f backend
docker-compose logs -f frontend
```

**Приложение будет доступно:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:5000
- pgAdmin (если запущен): http://localhost:5050

#### Серверная озвучка (TTS)
- Backend `/api/review` возвращает `tts_audio_data_url`, если удалось синтезировать аудио через Edge TTS или gTTS.
- Для стабильной работы Edge TTS используется `edge-tts==7.1.0`.
- Для `pt-PT` по умолчанию отключён фоллбэк на gTTS — включите через `ALLOW_PT_GTTs_FALLBACK=true`, если вас устраивает бразильский акцент.

### Шаг 6: Остановка приложения

```bash
# Остановить все контейнеры
docker-compose down

# Остановить и удалить volumes (база данных будет удалена!)
docker-compose down -v
```

## 🔧 Полезные команды Docker

### Управление контейнерами

```bash
# Перезапуск конкретного сервиса
docker-compose restart backend

# Пересборка после изменений в коде
docker-compose up -d --build

# Посмотреть логи последних 100 строк
docker-compose logs --tail=100 backend

# Войти в контейнер
docker-compose exec backend bash
docker-compose exec db psql -U diary_user -d diary_db
```

### Работа с базой данных

```bash
# Создать backup базы данных
docker-compose exec db pg_dump -U diary_user diary_db > backup.sql

# Восстановить из backup
docker-compose exec -T db psql -U diary_user diary_db < backup.sql

# Подключиться к PostgreSQL
docker-compose exec db psql -U diary_user -d diary_db
```

### Очистка Docker

```bash
# Удалить все остановленные контейнеры
docker container prune

# Удалить неиспользуемые images
docker image prune -a

# Удалить неиспользуемые volumes
docker volume prune

# Полная очистка (осторожно!)
docker system prune -a --volumes
```

## 📱 Использование pgAdmin (опционально)

pgAdmin - веб-интерфейс для управления PostgreSQL.

### Запуск с pgAdmin:

```bash
# Запустить с профилем tools
docker-compose --profile tools up -d
```

### Настройка pgAdmin:

1. Откройте http://localhost:5050
2. Войдите:
   - Email: `admin@diary.local`
   - Password: `admin123` (или ваш из .env)
3. Добавьте сервер:
   - Name: `Diary DB`
   - Host: `db`
   - Port: `5432`
   - Username: `diary_user`
   - Password: из вашего `.env`

## 🌐 Деплой в продакшн

### Подготовка к деплою

1. **Измените пароли в `.env`:**
```bash
# Генерация безопасных паролей
openssl rand -base64 32  # для DB_PASSWORD
openssl rand -hex 32     # для SECRET_KEY
```

2. **Обновите docker-compose.yml для продакшена:**

```yaml
# Добавьте в services.backend.environment:
FLASK_ENV: production
# Отключите debug режим
```

3. **Настройте HTTPS** (используйте nginx-proxy или Traefik)

### Деплой на VPS (DigitalOcean, Linode, Hetzner)

```bash
# На сервере установите Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Клонируйте проект
git clone your-repo.git
cd diary-app

# Создайте .env с production настройками
nano .env

# Запустите
docker-compose up -d

# Настройте автозапуск
sudo systemctl enable docker
```

### Рекомендуемые бесплатные VPS провайдеры:

1. **Oracle Cloud Free Tier**
   - 2 VM бесплатно навсегда
   - 1-4 OCPU, 1-24 GB RAM
   - https://www.oracle.com/cloud/free/

2. **Google Cloud Platform** (Free Tier)
   - $300 кредитов на 90 дней
   - e2-micro VM бесплатно
   - https://cloud.google.com/free

3. **AWS Free Tier**
   - t2.micro бесплатно 12 месяцев
   - https://aws.amazon.com/free/

## 🔐 Безопасность

### Важные настройки для продакшена:

1. **Измените все пароли по умолчанию**
2. **Используйте HTTPS (Let's Encrypt)**
3. **Настройте firewall:**

```bash
# Ubuntu/Debian
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable
```

4. **Ограничьте доступ к pgAdmin:**

```yaml
# В docker-compose.yml
pgadmin:
  networks:
    - internal  # Не exposed наружу
```

5. **Регулярные backup'ы:**

```bash
# Добавьте в crontab
0 2 * * * docker-compose exec db pg_dump -U diary_user diary_db > /backups/diary_$(date +\%Y\%m\%d).sql
```

## 🐛 Решение проблем

### Проблема: Контейнер backend падает

```bash
# Проверьте логи
docker-compose logs backend

# Часто проблема в неправильном GROQ_API_KEY
# Проверьте .env файл
```

### Проблема: Frontend не может подключиться к backend

```bash
# Проверьте что REACT_APP_API_URL правильный
# Пересоберите frontend
docker-compose up -d --build frontend
```

### Проблема: База данных не запускается

```bash
# Проверьте что порт 5432 свободен
sudo lsof -i :5432

# Удалите старые volumes и пересоздайте
docker-compose down -v
docker-compose up -d
```

### Проблема: Ошибка "Permission denied"

```bash
# Linux: дайте права на директории
sudo chown -R $USER:$USER .

# Или запустите с sudo (не рекомендуется)
sudo docker-compose up -d
```

### Проблема: Не работает запись аудио

- Проверьте что используете HTTPS или localhost
- Разрешите доступ к микрофону в браузере
- Проверьте поддержку MediaRecorder: https://caniuse.com/mediarecorder

## 📊 Мониторинг

### Просмотр ресурсов

```bash
# Использование ресурсов контейнерами
docker stats

# Размер images
docker images

# Размер volumes
docker volume ls
```

### Настройка логирования

Добавьте в `docker-compose.yml`:

```yaml
services:
  backend:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

## 🔄 Обновление приложения

```bash
# 1. Получите последние изменения
git pull

# 2. Пересоберите контейнеры
docker-compose up -d --build

# 3. Проверьте что все работает
docker-compose ps
docker-compose logs -f
```

## 📈 Масштабирование

### Запуск нескольких backend workers:

```bash
# В docker-compose.yml увеличьте workers в CMD
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "8", "app:app"]

# Или запустите несколько инстансов
docker-compose up -d --scale backend=3
```

### Добавление Redis для кеширования:

```yaml
# В docker-compose.yml
redis:
  image: redis:alpine
  ports:
    - "6379:6379"
```

## 🎯 Что дальше?

### Возможные улучшения:

1. **Хранение аудио файлов:**
   - AWS S3 / MinIO
   - Cloudinary

2. **Улучшенная транскрибация:**
   - Whisper Large V3 через Groq (уже есть)
   - Альтернатива: AssemblyAI, Deepgram

3. **Дополнительные функции:**
   - Экспорт в PDF/TXT
   - Теги и категории
   - Поиск по тексту
   - Аналитика (графики активности)

4. **CI/CD:**
   - GitHub Actions
   - Автоматический деплой

## 📚 Дополнительные ресурсы

- **Docker Documentation:** https://docs.docker.com
- **Docker Compose:** https://docs.docker.com/compose/
- **Groq API Docs:** https://console.groq.com/docs
- **PostgreSQL:** https://www.postgresql.org/docs/

---

**Готово к использованию! 🎉**

Если возникли проблемы - проверьте логи: `docker-compose logs -f`