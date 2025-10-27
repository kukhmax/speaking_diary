# 🚀 Полное руководство по установке Дневника v2.0

## 📋 Содержание

1. [Быстрая установка (5 минут)](#быстрая-установка)
2. [Детальная установка с объяснениями](#детальная-установка)
3. [Проверка установки](#проверка)
4. [Первое использование](#первое-использование)
5. [Что дальше?](#что-дальше)

---

## ⚡ Быстрая установка

**Для опытных пользователей - готово за 5 минут:**

```bash
# 1. Установите Docker (если нет)
curl -fsSL https://get.docker.com | sh

# 2. Клонируйте проект
git clone https://github.com/your-username/diary-app.git
cd diary-app

# 3. Получите API ключ: https://console.groq.com
# 4. Настройте .env
cp .env.example .env
echo "GROQ_API_KEY=gsk_ваш_ключ" >> .env

# 5. Запустите!
docker-compose up -d

# 6. Откройте http://localhost:3000
```

**Готово! 🎉**

---

## 📖 Детальная установка

### Шаг 1: Проверка системных требований

#### Минимальные требования:
- **RAM:** 2 GB
- **Диск:** 5 GB свободного места
- **OS:** Windows 10+, macOS 10.14+, Linux (любой современный дистрибутив)
- **Браузер:** Chrome 60+, Firefox 55+, Safari 11+, Edge 79+

#### Проверьте вашу систему:

```bash
# Проверка версии ОС
# Windows:
winver

# macOS:
sw_vers

# Linux:
lsb_release -a

# Проверка свободного места
df -h

# Проверка памяти
free -h  # Linux/macOS
```

---

### Шаг 2: Установка Docker

Docker нужен для запуска всех компонентов приложения в изолированных контейнерах.

#### Windows:

1. Скачайте [Docker Desktop для Windows](https://www.docker.com/products/docker-desktop)
2. Запустите установщик
3. Следуйте инструкциям
4. Перезагрузите компьютер
5. Запустите Docker Desktop

**Проверка:**
```powershell
docker --version
docker-compose --version
```

#### macOS:

**Вариант 1: Docker Desktop (рекомендуется)**
```bash
# Скачайте с https://www.docker.com/products/docker-desktop
# Или через Homebrew:
brew install --cask docker
```

**Вариант 2: Homebrew**
```bash
brew install docker docker-compose
```

**Проверка:**
```bash
docker --version
docker-compose --version
```

#### Linux (Ubuntu/Debian):

```bash
# Обновите систему
sudo apt update && sudo apt upgrade -y

# Установите Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Установите Docker Compose
sudo apt install docker-compose -y

# Добавьте пользователя в группу docker
sudo usermod -aG docker $USER

# ВАЖНО: Перезайдите в систему (logout/login)
# или выполните:
newgrp docker
```

**Проверка:**
```bash
docker --version
docker-compose --version

# Проверка без sudo
docker ps
```

#### Linux (CentOS/RHEL/Fedora):

```bash
# Установка
sudo dnf install -y docker docker-compose
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER

# Перезайдите в систему
```

---

### Шаг 3: Установка Git (если нет)

#### Windows:
Скачайте с https://git-scm.com/download/win

#### macOS:
```bash
brew install git
```

#### Linux:
```bash
sudo apt install git  # Ubuntu/Debian
sudo dnf install git  # CentOS/Fedora
```

**Проверка:**
```bash
git --version
```

---

### Шаг 4: Клонирование проекта

```bash
# Создайте директорию для проектов
mkdir -p ~/projects
cd ~/projects

# Клонируйте репозиторий
git clone https://github.com/your-username/diary-app.git

# Перейдите в директорию
cd diary-app

# Проверьте структуру
ls -la
```

**Вы должны увидеть:**
```
.
├── backend/
├── frontend/
├── nginx/
├── docker-compose.yml
├── docker-compose.prod.yml
├── .env.example
├── Makefile
└── README.md
```

---

### Шаг 5: Получение Groq API Key

Groq предоставляет **бесплатный** доступ к Whisper Large V3 для транскрибации.

#### 5.1 Регистрация

1. Откройте https://console.groq.com
2. Нажмите **Sign Up**
3. Зарегистрируйтесь через:
   - GitHub (рекомендуется)
   - Google
   - Email

#### 5.2 Создание API Key

1. После входа перейдите в **API Keys**
2. Нажмите **Create API Key**
3. Дайте имя (например, "Diary App")
4. Скопируйте ключ (начинается с `gsk_...`)
5. **ВАЖНО:** Сохраните ключ - он больше не будет показан!

#### 5.3 Проверка лимитов

- Бесплатно: **14,400 запросов в день**
- Достаточно для: ~240 записей по 1 минуте каждая
- Сбрасывается каждый день в 00:00 UTC

---

### Шаг 6: Настройка переменных окружения

#### 6.1 Создайте .env файл

```bash
cd ~/projects/diary-app

# Скопируйте шаблон
cp .env.example .env

# Откройте для редактирования
# Windows:
notepad .env

# macOS:
open -e .env

# Linux:
nano .env
# или
vim .env
```

#### 6.2 Заполните .env

```bash
# ===== ОБЯЗАТЕЛЬНО =====

# Groq API Key (вставьте ваш ключ)
GROQ_API_KEY=gsk_ваш_ключ_здесь

# Database Password (придумайте сильный пароль)
DB_PASSWORD=ваш_безопасный_пароль_123

# Flask Secret Key (случайная строка)
SECRET_KEY=придумайте_длинную_случайную_строку

# ===== ОПЦИОНАЛЬНО =====

# pgAdmin Password (если будете использовать)
PGADMIN_PASSWORD=admin_password_123

# API URL для фронтенда (по умолчанию - localhost)
REACT_APP_API_URL=http://localhost:5000/api

# Переопределения голосов Edge TTS (серверная озвучка)
# EDGE_TTS_VOICE=
# EDGE_TTS_PT_VOICE=

# Разрешить фоллбэк на gTTS для португальского (pt-PT)
# ВНИМАНИЕ: gTTS 'pt' использует бразильский акцент
ALLOW_PT_GTTs_FALLBACK=false
```

#### 6.3 Генерация безопасных паролей

**Вариант 1: OpenSSL**
```bash
# Для DB_PASSWORD
openssl rand -base64 32

# Для SECRET_KEY
openssl rand -hex 32
```

**Вариант 2: Python**
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Вариант 3: Онлайн**
https://www.random.org/strings/ (длина 32, буквы+цифры)

#### 6.4 Сохраните файл

```bash
# Проверьте что .env создан
ls -la | grep .env

# Должны увидеть:
# -rw-r--r-- 1 user user  xxx .env
```

---

### Шаг 7: Запуск приложения

#### 7.1 Сборка и запуск

```bash
# Вариант 1: Docker Compose
docker-compose up -d

# Вариант 2: Makefile (если доступен)
make up

# -d означает "detached mode" (фоновый режим)
```

#### 7.2 Первый запуск (занимает 2-5 минут)

Docker будет:
1. Скачивать образы (PostgreSQL, Python, Node)
2. Собирать ваши контейнеры
3. Создавать сети и volumes
4. Запускать сервисы

**Вы увидите:**
```
Creating network "diary_network" ... done
Creating volume "diary_postgres_data" ... done
Creating diary_db ... done
Creating diary_backend ... done
Creating diary_frontend ... done
```

#### 7.3 Проверка статуса

```bash
# Посмотрите запущенные контейнеры
docker-compose ps

# Должны увидеть (все в состоянии "Up"):
       Name                     Command               State           Ports
--------------------------------------------------------------------------------
diary_backend      gunicorn app:app              Up      0.0.0.0:5000->5000/tcp
diary_db           docker-entrypoint.sh postgres Up      5432/tcp
diary_frontend     nginx -g daemon off;          Up      0.0.0.0:3000->80/tcp
```

#### 7.4 Просмотр логов

```bash
# Все логи сразу
docker-compose logs -f

# Логи конкретного сервиса
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f db

# Последние 50 строк
docker-compose logs --tail=50

# Ctrl+C для выхода из просмотра логов
```

#### 7.5 Серверная озвучка (TTS)

- Эндпоинт `/api/review` проверяет текст (Gemini — при наличии ключа) и синтезирует аудио через Edge TTS (приоритет) или gTTS (фоллбэк).
- Для португальского (`pt-PT`) фоллбэк на gTTS отключён по умолчанию — включите `ALLOW_PT_GTTs_FALLBACK=true`, если устраивает бразильский акцент.
- Пример запроса (Windows PowerShell, устойчиво к юникоду):
```powershell
$body = @{ text = "Hola, qué tal"; language = "es-ES" } | ConvertTo-Json
Invoke-RestMethod -Uri http://localhost:5000/api/review -Method Post -ContentType "application/json" -Body $body
```
- Если `tts_audio_data_url` не вернулся, используйте на фронтенде «Speak (browser)» и убедитесь, что в OS установлены системные голоса нужного языка (иначе браузер может озвучивать по умолчанию на `en-US`).

---

## ✅ Проверка

### 1. Проверка контейнеров

```bash
docker-compose ps

# ВСЕ должны быть "Up"
# Если какой-то "Exit" - смотрите логи
```

### 2. Health Check

```bash
# Проверка backend API
curl http://localhost:5000/api/health

# Должны увидеть:
# {"status":"ok","message":"Server is running"}

# Если команды curl нет:
# Windows: использ уйте браузер или PowerShell Invoke-WebRequest
# macOS/Linux: установите curl
```

### 3. Проверка в браузере

Откройте:
- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:5000/api/health

**Должны увидеть:**
- Красивый интерфейс с кнопкой "Создать запись"
- JSON ответ от API

### 4. Проверка базы данных

```bash
# Подключитесь к PostgreSQL
docker-compose exec db psql -U diary_user -d diary_db

# Внутри PostgreSQL:
\dt  # список таблиц (должна быть таблица "entry")
\q   # выход
```

---

## 🎯 Первое использование

### 1. Откройте приложение

```
http://localhost:3000
```

### 2. Создайте первую запись

1. Нажмите **"Создать запись"**
2. Выберите язык (например, "Русский")
3. Нажмите на микрофон 🎤
4. Разрешите доступ к микрофону (если браузер спросит)
5. Скажите что-нибудь (например: "Это моя первая запись")
6. Нажмите ⏹️ (остановить)
7. Дождитесь транскрибации (2-5 секунд)
8. Проверьте текст
9. Нажмите **"Сохранить"**

### 3. Просмотрите записи

- Запись появится в списке под текущей датой
- Кликните на дату чтобы развернуть/свернуть
- Показывается время и длительность

---

## 🔧 Что дальше?

### Для разработки

1. **Изучите код:**
   ```bash
   # Backend API
   less backend/app.py
   
   # Frontend UI
   less frontend/src/App.js
   ```

2. **Внесите изменения:**
   - Код обновляется автоматически (hot reload)
   - Backend: перезапустите контейнер `docker-compose restart backend`
   - Frontend: изменения применяются моментально

3. **Документация:**
   - [README-DOCKER.md](README-DOCKER.md) - детали Docker
   - [QUICK-REFERENCE.md](QUICK-REFERENCE.md) - команды
   - [PROJECT-STRUCTURE.md](PROJECT-STRUCTURE.md) - структура

### Для продакшена

1. **Прочитайте руководство по деплою:**
   ```bash
   cat DEPLOY.md
   ```

2. **Выберите VPS провайдера** (см. DEPLOY.md)

3. **Настройте домен и SSL:**
   - Получите домен
   - Настройте DNS
   - Установите SSL через Let's Encrypt

4. **Запустите в продакшене:**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

### Дополнительные функции

1. **Включите pgAdmin** (веб-интерфейс для PostgreSQL):
   ```bash
   docker-compose --profile tools up -d
   # Откройте http://localhost:5050
   ```

2. **Настройте автоматические backup'ы:**
   ```bash
   # Создайте cron задачу
   crontab -e
   
   # Добавьте (backup каждый день в 2 AM):
   0 2 * * * cd /path/to/diary-app && make backup
   ```

3. **Настройте мониторинг:**
   - Зарегистрируйтесь на https://uptimerobot.com
   - Добавьте http://your-domain.com/api/health
   - Получайте уведомления при падении

---

## 🐛 Решение проблем при установке

### Проблема: Docker не запускается

**Windows:**
```powershell
# Проверьте виртуализацию
systeminfo | findstr "Hyper-V"

# Если не включено - включите в BIOS:
# 1. Перезагрузите компьютер
# 2. Войдите в BIOS (обычно F2 или Del)
# 3. Включите Intel VT-x или AMD-V
# 4. Сохраните и перезагрузите
```

**Linux:**
```bash
# Проверьте статус службы
sudo systemctl status docker

# Если не запущена - запустите
sudo systemctl start docker
sudo systemctl enable docker

# Проверьте права
groups $USER  # должно быть "docker"

# Если нет - добавьте и перезайдите
sudo usermod -aG docker $USER
```

### Проблема: Порт уже занят

```bash
# Проверьте какие порты заняты
# Linux/macOS:
sudo lsof -i :3000
sudo lsof -i :5000
sudo lsof -i :5432

# Windows PowerShell:
netstat -ano | findstr :3000
netstat -ano | findstr :5000
netstat -ano | findstr :5432

# Решение: Остановите процесс или измените порт
# Для изменения портов отредактируйте docker-compose.yml:
ports:
  - "8080:80"  # вместо 3000:80
```

### Проблема: GROQ_API_KEY не работает

```bash
# Проверьте что ключ правильно прописан
cat .env | grep GROQ_API_KEY

# Должно быть (без пробелов):
GROQ_API_KEY=gsk_ваш_ключ

# НЕ должно быть:
# GROQ_API_KEY = gsk_ваш_ключ  ❌ (пробелы)
# GROQ_API_KEY="gsk_ваш_ключ"  ❌ (кавычки не нужны)

# Перезапустите после изменения .env
docker-compose restart backend
```

### Проблема: Контейнеры падают

```bash
# Посмотрите логи
docker-compose logs --tail=50

# Часто это:
# 1. Неправильный .env
# 2. Недостаточно памяти
# 3. Конфликт портов

# Проверьте память
free -h  # Linux/macOS
# Должно быть минимум 2 GB свободно

# Полная перезагрузка
docker-compose down -v
docker-compose up -d --build
```

### Проблема: Frontend не подключается к Backend

```bash
# Проверьте сеть Docker
docker network ls
docker network inspect diary_network

# Проверьте что все контейнеры в одной сети
docker-compose ps

# Проверьте CORS
docker-compose logs backend | grep CORS

# Если проблема - убедитесь что в backend/app.py:
# CORS(app)  # без ограничений для localhost
```

### Проблема: Микрофон не работает

**В браузере:**
1. Используйте HTTPS или localhost (HTTP не работает)
2. Разрешите доступ к микрофону в настройках браузера
3. Проверьте что микрофон работает в системе

**Chrome:**
- Settings → Privacy and security → Site Settings → Microphone
- Разрешите для http://localhost:3000

**Firefox:**
- Preferences → Privacy & Security → Permissions → Microphone
- Settings для http://localhost:3000

**Safari:**
- Safari → Preferences → Websites → Microphone
- Разрешите для localhost

### Проблема: База данных не создаётся

```bash
# Проверьте что volume создан
docker volume ls | grep postgres

# Проверьте логи PostgreSQL
docker-compose logs db

# Если ошибки инициализации - пересоздайте
docker-compose down -v  # ВНИМАНИЕ: удалит данные!
docker-compose up -d

# База создастся автоматически при первом запуске backend
```

---

## 📊 Проверочный список

После установки проверьте что всё работает:

- [ ] Docker установлен (`docker --version`)
- [ ] Docker Compose установлен (`docker-compose --version`)
- [ ] Проект склонирован
- [ ] .env файл создан и заполнен
- [ ] GROQ_API_KEY получен и добавлен
- [ ] Контейнеры запущены (`docker-compose ps` - все "Up")
- [ ] Backend отвечает (http://localhost:5000/api/health)
- [ ] Frontend открывается (http://localhost:3000)
- [ ] База данных работает (`docker-compose exec db psql -U diary_user -d diary_db`)
- [ ] Можно создать запись
- [ ] Микрофон работает
- [ ] Транскрибация работает
- [ ] Записи сохраняются и отображаются

**Если все пункты ✅ - установка успешна! 🎉**

---

## 🎓 Обучение

### Для новичков в Docker

1. **Основы Docker:**
   ```bash
   # Посмотреть запущенные контейнеры
   docker ps
   
   # Остановить контейнер
   docker stop diary_backend
   
   # Запустить контейнер
   docker start diary_backend
   
   # Войти в контейнер
   docker exec -it diary_backend bash
   
   # Посмотреть логи
   docker logs diary_backend
   ```

2. **Основы Docker Compose:**
   ```bash
   # Запустить сервисы
   docker-compose up -d
   
   # Остановить сервисы
   docker-compose down
   
   # Перезапустить сервисы
   docker-compose restart
   
   # Посмотреть статус
   docker-compose ps
   
   # Пересобрать и запустить
   docker-compose up -d --build
   ```

3. **Полезные ресурсы:**
   - Docker Tutorial: https://docker-curriculum.com
   - Docker Compose Docs: https://docs.docker.com/compose/
   - Docker Cheat Sheet: https://github.com/wsargent/docker-cheat-sheet

### Для разработчиков

1. **Структура кода:**
   - Backend: `backend/app.py` - Flask REST API
   - Frontend: `frontend/src/App.js` - React компонент
   - API клиент: `frontend/src/api.js`

2. **Как добавить новый API endpoint:**
   ```python
   # В backend/app.py:
   @app.route('/api/my-endpoint', methods=['GET'])
   def my_endpoint():
       return jsonify({'message': 'Hello'})
   
   # В frontend/src/api.js:
   export const myEndpoint = async () => {
       const response = await axios.get(`${API_BASE_URL}/my-endpoint`);
       return response.data;
   };
   ```

3. **Hot reload:**
   - Frontend: Изменения применяются автоматически
   - Backend: Нужен перезапуск `docker-compose restart backend`

---

## 🌟 Советы по использованию

### Оптимизация производительности

1. **Увеличьте memory для Docker:**
   - Docker Desktop → Settings → Resources → Memory: 4 GB

2. **Используйте SSD для volumes:**
   ```bash
   # Переместите Docker volumes на SSD (если возможно)
   ```

3. **Очищайте неиспользуемые данные:**
   ```bash
   docker system prune -f
   docker volume prune -f
   ```

### Безопасность

1. **Никогда не коммитьте .env в Git:**
   ```bash
   # .env уже в .gitignore, но проверьте:
   cat .gitignore | grep .env
   ```

2. **Используйте сильные пароли:**
   ```bash
   # Минимум 16 символов, буквы + цифры + спецсимволы
   ```

3. **Регулярно обновляйте зависимости:**
   ```bash
   docker-compose pull  # Обновить образы
   docker-compose up -d --build  # Пересобрать
   ```

### Backup и восстановление

1. **Создавайте регулярные backup'ы:**
   ```bash
   # Вручную
   make backup
   
   # Или автоматически через cron
   crontab -e
   0 2 * * * cd /path/to/diary-app && make backup
   ```

2. **Храните backup'ы в безопасном месте:**
   ```bash
   # Копируйте в облако
   cp backups/*.sql.gz /path/to/cloud-storage/
   
   # Или используйте rclone/rsync
   ```

---

## 📞 Получение помощи

### Самостоятельная диагностика

1. **Проверьте логи:**
   ```bash
   docker-compose logs -f
   ```

2. **Проверьте статус:**
   ```bash
   docker-compose ps
   make check  # Если Makefile установлен
   ```

3. **Поищите в документации:**
   - [README-DOCKER.md](README-DOCKER.md)
   - [QUICK-REFERENCE.md](QUICK-REFERENCE.md)
   - [DEPLOY.md](DEPLOY.md)

### Сообщество

1. **GitHub Issues:**
   - Поищите похожую проблему
   - Создайте новый issue с логами

2. **Stack Overflow:**
   - Теги: docker, flask, react, postgresql

3. **Discord/Slack:**
   - Docker Community
   - React Community

---

## 🎉 Поздравляем!

Вы успешно установили **Дневник v2.0**!

### Что дальше?

1. ✅ **Используйте приложение** - создавайте записи
2. 📖 **Изучите документацию** - узнайте все возможности
3. 🚀 **Деплой в продакшн** - сделайте доступным онлайн
4. 🛠️ **Кастомизация** - адаптируйте под свои нужды
5. 🤝 **Вносите вклад** - улучшайте проект

### Полезные ссылки

- **[README.md](README.md)** - обзор проекта
- **[README-DOCKER.md](README-DOCKER.md)** - Docker детали
- **[DEPLOY.md](DEPLOY.md)** - деплой в продакшн
- **[QUICK-REFERENCE.md](QUICK-REFERENCE.md)** - команды
- **[CHANGELOG.md](CHANGELOG.md)** - история версий

---

<div align="center">

**Приятного использования! 🚀**

Если что-то не работает - не паникуйте!
Проверьте логи: `docker-compose logs -f`

[GitHub](https://github.com/your-username/diary-app) • [Документация](README.md) • [Поддержка](https://github.com/your-username/diary-app/issues)

</div>