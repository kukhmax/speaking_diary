# 🚀 Руководство по деплою в продакшн

## 📋 Содержание

1. [Подготовка к деплою](#подготовка)
2. [Деплой на VPS](#деплой-на-vps)
3. [Настройка домена и SSL](#настройка-домена)
4. [Автоматический деплой через GitHub Actions](#cicd)
5. [Мониторинг и обслуживание](#мониторинг)

---

## 🔧 Подготовка

### 1. Выбор VPS провайдера

**Бесплатные варианты:**

| Провайдер | Ресурсы | Срок | Ссылка |
|-----------|---------|------|--------|
| Oracle Cloud | 2 VM (1-4 CPU, 1-24GB RAM) | Навсегда | https://www.oracle.com/cloud/free/ |
| Google Cloud | $300 кредитов | 90 дней | https://cloud.google.com/free |
| AWS | t2.micro | 12 месяцев | https://aws.amazon.com/free |
| Azure | $200 кредитов | 30 дней | https://azure.microsoft.com/free/ |

**Платные (рекомендуемые):**

| Провайдер | Цена/месяц | Ресурсы |
|-----------|------------|---------|
| DigitalOcean | $6 | 1 CPU, 1GB RAM, 25GB SSD |
| Hetzner | €4.5 | 1 CPU, 2GB RAM, 20GB SSD |
| Linode | $5 | 1 CPU, 1GB RAM, 25GB SSD |

### 2. Требования к серверу

**Минимальные:**
- 1 CPU
- 1GB RAM
- 10GB диск
- Ubuntu 22.04 LTS

**Рекомендуемые:**
- 2 CPU
- 2GB RAM
- 20GB SSD
- Ubuntu 22.04 LTS

---

## 🌐 Деплой на VPS

### Шаг 1: Подключение к серверу

```bash
# Подключитесь по SSH
ssh root@your-server-ip

# Обновите систему
apt update && apt upgrade -y
```

### Шаг 2: Установка Docker

```bash
# Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Установка Docker Compose
apt install docker-compose -y

# Добавьте текущего пользователя в группу docker
usermod -aG docker $USER

# Включите автозапуск Docker
systemctl enable docker
systemctl start docker

# Проверка
docker --version
docker-compose --version
```

### Шаг 3: Клонирование проекта

```bash
# Создайте директорию для проекта
mkdir -p /var/www
cd /var/www

# Клонируйте репозиторий
git clone https://github.com/your-username/diary-app.git
cd diary-app

# Или загрузите файлы вручную
# scp -r ./diary-app root@your-server-ip:/var/www/
```

### Шаг 4: Настройка переменных окружения

```bash
# Создайте .env файл
nano .env
```

**Содержимое .env для продакшена:**

```bash
# Database
DB_PASSWORD=СИЛЬНЫЙ_ПАРОЛЬ_123_ИЗМЕНИТЕ

# Groq API (бесплатно)
GROQ_API_KEY=gsk_ваш_ключ_с_console_groq_com

# Flask
SECRET_KEY=ИСПОЛЬЗУЙТЕ_ДЛИННЫЙ_СЛУЧАЙНЫЙ_КЛЮЧ

# Production API URL
PRODUCTION_API_URL=https://your-domain.com/api

# pgAdmin (опционально)
PGADMIN_PASSWORD=АДМИН_ПАРОЛЬ_123
```

**Генерация безопасных паролей:**

```bash
# Для DB_PASSWORD
openssl rand -base64 32

# Для SECRET_KEY
openssl rand -hex 32
```

Подробно о генерации и управлении секретами см. в разделе: [SECRETS-GENERATION.md](SECRETS-GENERATION.md).

### Шаг 5: Настройка Firewall

```bash
# Установите UFW
apt install ufw -y

# Разрешите SSH, HTTP, HTTPS
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp

# Включите firewall
ufw enable

# Проверьте статус
ufw status
```

### Шаг 6: Запуск приложения

```bash
# Сборка и запуск
docker-compose -f docker-compose.prod.yml up -d --build

# Проверка логов
docker-compose -f docker-compose.prod.yml logs -f

# Проверка статуса
docker-compose -f docker-compose.prod.yml ps
```

---

## 🔐 Настройка домена и SSL

### Шаг 1: Настройка DNS

Добавьте A-записи у вашего DNS провайдера:

```
A     @              your-server-ip
A     www            your-server-ip
```

**Бесплатные домены:**
- Freenom: https://www.freenom.com (бесплатные .tk, .ml, .ga)
- No-IP: https://www.noip.com (бесплатные поддомены)

**Платные (рекомендуется):**
- Namecheap: ~$10/год
- Cloudflare: ~$10/год
- Google Domains: ~$12/год

### Шаг 2: Получение SSL сертификата (Let's Encrypt)

```bash
# Остановите приложение
docker-compose -f docker-compose.prod.yml down

# Создайте директорию для Nginx конфигурации
mkdir -p nginx

# Скопируйте nginx.conf в nginx/nginx.conf
# Замените "your-domain.com" на ваш домен

# Получите SSL сертификат
docker run -it --rm \
  -v $(pwd)/nginx/ssl:/etc/letsencrypt \
  -v $(pwd)/certbot_data:/var/www/certbot \
  -p 80:80 \
  certbot/certbot certonly --standalone \
  --email your-email@example.com \
  --agree-tos \
  -d your-domain.com -d www.your-domain.com

# Запустите приложение с SSL
docker-compose -f docker-compose.prod.yml up -d
```

### Шаг 3: Автоматическое обновление SSL

SSL сертификаты обновляются автоматически через контейнер certbot в docker-compose.prod.yml

Проверка обновления вручную:

```bash
docker-compose -f docker-compose.prod.yml exec certbot certbot renew --dry-run
```

---

## 🤖 CI/CD с GitHub Actions

### Настройка автоматического деплоя

Создайте `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Production

on:
  push:
    branches: [ main ]
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v3
    
    - name: Deploy to VPS
      uses: appleboy/ssh-action@master
      with:
        host: ${{ secrets.VPS_HOST }}
        username: ${{ secrets.VPS_USERNAME }}
        key: ${{ secrets.VPS_SSH_KEY }}
        script: |
          cd /var/www/diary-app
          git pull origin main
          docker-compose -f docker-compose.prod.yml up -d --build
          docker system prune -f
    
    - name: Health Check
      run: |
        sleep 30
        curl -f https://your-domain.com/api/health || exit 1
```

### Настройка GitHub Secrets

В репозитории GitHub → Settings → Secrets → Actions:

```
VPS_HOST: your-server-ip
VPS_USERNAME: root
VPS_SSH_KEY: [содержимое ~/.ssh/id_rsa]
```

**Создание SSH ключа:**

```bash
# На вашем компьютере
ssh-keygen -t rsa -b 4096 -C "deploy@diary-app"

# Скопируйте публичный ключ на сервер
ssh-copy-id root@your-server-ip

# Скопируйте приватный ключ в GitHub Secrets
cat ~/.ssh/id_rsa
```

---

## 📊 Мониторинг и обслуживание

### Настройка логирования

```bash
# Просмотр логов в реальном времени
docker-compose -f docker-compose.prod.yml logs -f

# Логи конкретного сервиса
docker-compose -f docker-compose.prod.yml logs -f backend

# Последние 100 строк
docker-compose -f docker-compose.prod.yml logs --tail=100
```

### Мониторинг ресурсов

```bash
# Использование ресурсов контейнерами
docker stats

# Использование диска
df -h

# Свободная память
free -h

# Загрузка процессора
htop
```

### Автоматические backup'ы

Создайте скрипт `/var/www/diary-app/backup.sh`:

```bash
#!/bin/bash

BACKUP_DIR="/var/backups/diary-app"
DATE=$(date +%Y%m%d_%H%M%S)

# Создайте директорию для backup'ов
mkdir -p $BACKUP_DIR

# Backup базы данных
docker-compose -f /var/www/diary-app/docker-compose.prod.yml exec -T db \
  pg_dump -U diary_user diary_db > $BACKUP_DIR/db_backup_$DATE.sql

# Сжатие
gzip $BACKUP_DIR/db_backup_$DATE.sql

# Удаление старых backup'ов (старше 7 дней)
find $BACKUP_DIR -type f -name "*.gz" -mtime +7 -delete

echo "Backup completed: $BACKUP_DIR/db_backup_$DATE.sql.gz"
```

**Настройка cron:**

```bash
# Сделайте скрипт исполняемым
chmod +x /var/www/diary-app/backup.sh

# Откройте crontab
crontab -e

# Добавьте задачу (backup каждый день в 2:00 AM)
0 2 * * * /var/www/diary-app/backup.sh >> /var/log/diary-backup.log 2>&1
```

### Восстановление из backup

```bash
# Найдите нужный backup
ls -lh /var/backups/diary-app/

# Распакуйте
gunzip /var/backups/diary-app/db_backup_YYYYMMDD_HHMMSS.sql.gz

# Восстановите базу данных
docker-compose -f docker-compose.prod.yml exec -T db \
  psql -U diary_user diary_db < /var/backups/diary-app/db_backup_YYYYMMDD_HHMMSS.sql
```

### Мониторинг с Uptime Robot (бесплатно)

1. Зарегистрируйтесь на https://uptimerobot.com
2. Создайте новый монитор:
   - Type: HTTP(s)
   - URL: https://your-domain.com/api/health
   - Monitoring Interval: 5 минут
3. Настройте уведомления по email/Telegram/Slack

---

## 🔄 Обновление приложения

### Ручное обновление

```bash
cd /var/www/diary-app

# Получите последние изменения
git pull origin main

# Пересоберите и перезапустите
docker-compose -f docker-compose.prod.yml up -d --build

# Проверьте статус
docker-compose -f docker-compose.prod.yml ps
```

### С использованием Makefile

```bash
# Обновление одной командой
make -f Makefile prod-update

# Где prod-update в Makefile:
prod-update:
	git pull origin main
	docker-compose -f docker-compose.prod.yml up -d --build
	docker system prune -f
```

---

## 🛡️ Безопасность

### 1. Отключите root login по SSH

```bash
# Создайте нового пользователя
adduser deploy
usermod -aG sudo deploy
usermod -aG docker deploy

# Настройте SSH
nano /etc/ssh/sshd_config

# Измените:
PermitRootLogin no
PasswordAuthentication no

# Перезапустите SSH
systemctl restart sshd
```

### 2. Fail2ban для защиты от брутфорса

```bash
# Установка
apt install fail2ban -y

# Создайте конфигурацию
nano /etc/fail2ban/jail.local
```

```ini
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true
port = 22
logpath = /var/log/auth.log
```

```bash
# Запустите Fail2ban
systemctl enable fail2ban
systemctl start fail2ban

# Проверка статуса
fail2ban-client status sshd
```

### 3. Регулярные обновления системы

```bash
# Автоматические обновления безопасности
apt install unattended-upgrades -y
dpkg-reconfigure -plow unattended-upgrades
```

### 4. Защита от DDoS (Cloudflare)

1. Зарегистрируйтесь на https://cloudflare.com (бесплатно)
2. Добавьте ваш домен
3. Измените NS записи у регистратора домена
4. Включите проксирование (оранжевое облако)
5. Настройте правила firewall

---

## 📈 Оптимизация производительности

### 1. Redis для кеширования

Добавьте в `docker-compose.prod.yml`:

```yaml
redis:
  image: redis:alpine
  container_name: diary_redis
  restart: always
  networks:
    - internal
  command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
```

### 2. Оптимизация PostgreSQL

```bash
# Войдите в контейнер
docker-compose exec db bash

# Отредактируйте конфигурацию
nano /var/lib/postgresql/data/postgresql.conf
```

```ini
# Memory
shared_buffers = 256MB
effective_cache_size = 1GB

# Connections
max_connections = 100

# Logging
log_min_duration_statement = 1000
```

### 3. Масштабирование backend

```yaml
# В docker-compose.prod.yml
backend:
  # ... другие настройки
  deploy:
    replicas: 3
  command: gunicorn --bind 0.0.0.0:5000 --workers 4 --timeout 120 app:app
```

---

## 🐛 Решение проблем

### Проблема: Сайт недоступен

```bash
# Проверьте статус контейнеров
docker-compose -f docker-compose.prod.yml ps

# Проверьте логи
docker-compose -f docker-compose.prod.yml logs --tail=50

# Проверьте firewall
ufw status

# Проверьте Nginx
docker-compose -f docker-compose.prod.yml exec nginx nginx -t
```

### Проблема: SSL не работает

```bash
# Проверьте сертификаты
ls -la nginx/ssl/live/your-domain.com/

# Пересоздайте сертификаты
docker-compose -f docker-compose.prod.yml down
# Повторите шаг получения SSL

# Проверьте права
chmod -R 755 nginx/ssl/
```

### Проблема: База данных не запускается

```bash
# Проверьте логи
docker-compose -f docker-compose.prod.yml logs db

# Проверьте пространство на диске
df -h

# Пересоздайте volume (ВНИМАНИЕ: удалит данные!)
docker-compose -f docker-compose.prod.yml down -v
docker-compose -f docker-compose.prod.yml up -d
```

### Проблема: Out of Memory

```bash
# Добавьте swap
fallocate -l 2G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile

# Сделайте постоянным
echo '/swapfile none swap sw 0 0' >> /etc/fstab
```

---

## 📞 Поддержка

### Полезные команды

```bash
# Перезапуск всех сервисов
docker-compose -f docker-compose.prod.yml restart

# Полная очистка и перезапуск
docker-compose -f docker-compose.prod.yml down
docker system prune -a -f
docker-compose -f docker-compose.prod.yml up -d --build

# Экспорт логов
docker-compose -f docker-compose.prod.yml logs > logs_$(date +%Y%m%d).txt
```

### Мониторинг health check

```bash
# Скрипт проверки здоровья
curl -f https://your-domain.com/api/health || echo "API is down!"
```

---

**Готово к продакшену! 🎉**

Не забудьте:
- ✅ Изменить все пароли в `.env`
- ✅ Настроить backup'ы
- ✅ Включить мониторинг
- ✅ Настроить SSL
- ✅ Протестировать восстановление из backup