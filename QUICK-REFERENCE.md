# 📝 Быстрая справка по командам

## 🚀 Локальная разработка

```bash
# Первый запуск
make install

# Запуск
make up
# или
docker-compose up -d

# Остановка
make down
# или
docker-compose down

# Перезапуск
make restart

# Просмотр логов
make logs
make logs-backend
make logs-frontend

# Пересборка
make rebuild
```

## 🌐 Продакшн

```bash
# Запуск
docker-compose -f docker-compose.prod.yml up -d

# Остановка
docker-compose -f docker-compose.prod.yml down

# Обновление
git pull
docker-compose -f docker-compose.prod.yml up -d --build

# Логи
docker-compose -f docker-compose.prod.yml logs -f
```

## 🗄️ База данных

```bash
# Backup
make backup
# или
docker-compose exec -T db pg_dump -U diary_user diary_db > backup.sql

# Restore
docker-compose exec -T db psql -U diary_user diary_db < backup.sql

# Подключение к PostgreSQL
make shell-db
# или
docker-compose exec db psql -U diary_user -d diary_db

# SQL команды:
\dt                    # список таблиц
\d entry              # структура таблицы
SELECT * FROM entry;  # выбрать все записи
\q                    # выход
```

## 🔍 Мониторинг

```bash
# Статус контейнеров
docker-compose ps

# Использование ресурсов
docker stats

# Health check
make check
# или
curl http://localhost:5000/api/health
```

## 🐛 Отладка

```bash
# Войти в контейнер backend
docker-compose exec backend bash

# Войти в контейнер frontend
docker-compose exec frontend sh

# Проверить сеть
docker network ls
docker network inspect diary_network

# Перезапуск конкретного сервиса
docker-compose restart backend
```

## 🧹 Очистка

```bash
# Мягкая очистка
make clean

# Полная очистка (удаляет volumes!)
make clean-all

# Очистка Docker
docker system prune -f
docker volume prune -f
docker image prune -a -f
```

## 🔐 SSL (Продакшн)

```bash
# Получить сертификат
docker run -it --rm \
  -v $(pwd)/nginx/ssl:/etc/letsencrypt \
  -p 80:80 certbot/certbot certonly --standalone \
  --email you@example.com -d yourdomain.com

# Обновить сертификат
docker-compose exec certbot certbot renew

# Тест обновления
docker-compose exec certbot certbot renew --dry-run
```

## 📦 API эндпоинты

```bash
# Health check
curl http://localhost:5000/api/health

# Получить все записи
curl http://localhost:5000/api/entries

# Создать запись
curl -X POST http://localhost:5000/api/entries \
  -H "Content-Type: application/json" \
  -d '{"text":"Тестовая запись","language":"ru-RU"}'

# Транскрибация аудио
curl -X POST http://localhost:5000/api/transcribe \
  -F "audio=@recording.webm" \
  -F "language=ru-RU"

# Поиск
curl "http://localhost:5000/api/search?q=тест"
```

## 🔧 Переменные окружения

```bash
# .env файл должен содержать:
DB_PASSWORD=your_password
GROQ_API_KEY=gsk_your_key
SECRET_KEY=your_secret
```

## 📊 Полезные SQL запросы

```sql
-- Количество записей
SELECT COUNT(*) FROM entry;

-- Записи за сегодня
SELECT * FROM entry 
WHERE DATE(timestamp) = CURRENT_DATE;

-- Записи по языкам
SELECT language, COUNT(*) 
FROM entry 
GROUP BY language;

-- Удалить все записи (осторожно!)
DELETE FROM entry;

-- Удалить старые записи (старше 30 дней)
DELETE FROM entry 
WHERE timestamp < NOW() - INTERVAL '30 days';
```

## 🚨 Экстренные действия

```bash
# Приложение не отвечает - полный перезапуск
docker-compose down && docker-compose up -d

# База данных поломалась
docker-compose down -v  # ВНИМАНИЕ: удалит данные
docker-compose up -d

# Диск заполнен
docker system prune -a -f --volumes

# Сервер перезагрузился
cd /var/www/diary-app
docker-compose -f docker-compose.prod.yml up -d
```

## 📱 Тестирование

```bash
# Тест backend
curl http://localhost:5000/api/health

# Тест frontend
curl http://localhost:3000

# Тест базы данных
docker-compose exec db pg_isready -U diary_user

# Все тесты сразу
make check
```

## 🔄 Git workflow

```bash
# Обновить код на сервере
ssh user@server
cd /var/www/diary-app
git pull
docker-compose -f docker-compose.prod.yml up -d --build

# Откатить изменения
git log --oneline
git checkout COMMIT_HASH
docker-compose -f docker-compose.prod.yml up -d --build
```

## 🎯 Горячие клавиши Docker

```bash
Ctrl+C          # Выход из логов
Ctrl+D          # Выход из контейнера
Ctrl+P Ctrl+Q   # Отсоединиться от контейнера без остановки
```

## 📞 Быстрые ссылки

- Frontend: http://localhost:3000
- Backend API: http://localhost:5000
- Health check: http://localhost:5000/api/health
- pgAdmin: http://localhost:5050
- Groq Console: https://console.groq.com
- Docker Hub: https://hub.docker.com

## 🆘 Если ничего не помогает

```bash
# Остановите всё
docker-compose down -v

# Удалите всё Docker
docker system prune -a -f --volumes

# Заново клонируйте проект
rm -rf diary-app
git clone your-repo.git
cd diary-app

# Настройте .env
cp .env.example .env
nano .env

# Запустите
docker-compose up -d --build
```

---

## 🎓 Частые вопросы

**Q: Как изменить порт?**
```yaml
# В docker-compose.yml измените:
ports:
  - "8080:80"  # вместо 3000:80
```

**Q: Как добавить больше памяти контейнеру?**
```yaml
backend:
  deploy:
    resources:
      limits:
        memory: 1G
```

**Q: Как посмотреть размер базы данных?**
```sql
SELECT pg_size_pretty(pg_database_size('diary_db'));
```

**Q: Как экспортировать все записи в JSON?**
```bash
docker-compose exec db psql -U diary_user diary_db \
  -c "COPY (SELECT row_to_json(entry) FROM entry) TO STDOUT" > entries.json
```

---

**Сохраните эту страницу в закладки! 🔖**