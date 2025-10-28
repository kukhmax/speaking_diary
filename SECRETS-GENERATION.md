# Генерация и управление секретами

Коротко: генерируйте криптостойкие случайные строки на сервере и храните их в `.env`. Не впечатывайте секреты в Dockerfile и не коммитьте их в Git.

## Какие секреты нужны
- `DB_PASSWORD` — пароль для пользователя БД `diary_user`.
- `SECRET_KEY` — секрет для Flask (подпись сессий и токенов).
- `PGADMIN_PASSWORD` — пароль для pgAdmin (необязателен; используется только в dev-профиле).
- `GROQ_API_KEY` — ключ от провайдера; НЕ генерируется локально.

Требования:
- Длина: минимум 32 байта для `DB_PASSWORD` и 64 байта для `SECRET_KEY`.
- Формат: hex, base64 или urlsafe — любой подходит.

## Генерация секретов по системам

### Linux/macOS (Shell)
- `DB_PASSWORD`:
  - `openssl rand -hex 32`
  - или `openssl rand -base64 48`
- `SECRET_KEY`:
  - `python3 -c "import secrets; print(secrets.token_urlsafe(64))"`
  - или `openssl rand -base64 64`

### Windows (PowerShell)
- `DB_PASSWORD`:
  - `$b = New-Object 'System.Byte[]' 32; [System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($b); [Convert]::ToBase64String($b)`
- `SECRET_KEY`:
  - `$b = New-Object 'System.Byte[]' 64; [System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($b); [Convert]::ToBase64String($b)`
- Альтернатива (Python везде):
  - `python -c "import secrets; print(secrets.token_urlsafe(32))"` (DB_PASSWORD)
  - `python -c "import secrets; print(secrets.token_urlsafe(64))"` (SECRET_KEY)

## Заполнение `.env`
- Скопируйте пример: `cp .env.example .env` (Windows: `copy .env.example .env`).
- Заполните значения:
  - `DB_PASSWORD=<сгенерированное>`
  - `SECRET_KEY=<сгенерированное>`
  - `GROQ_API_KEY=<ваш_ключ>`
  - `PGADMIN_PASSWORD=<необязательный>`
- Правила:
  - Не используйте кавычки вокруг значений.
  - Не коммитьте `.env` в Git.

## Временная передача через окружение (без файла `.env`)
Если хотите один раз запустить без файла:
- Linux/macOS:
  - `export DB_PASSWORD=$(openssl rand -hex 32)`
  - `export SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(64))")`
  - `docker compose -f docker_compose_prod.yml up -d --build`
- Windows PowerShell:
  - `$env:DB_PASSWORD = python -c "import secrets; print(secrets.token_urlsafe(32))"`
  - `$env:SECRET_KEY = python -c "import secrets; print(secrets.token_urlsafe(64))"`
  - `docker compose -f docker_compose_prod.yml up -d --build`
- Важно: сохраните эти значения и перенесите в `.env`, иначе при следующем запуске новые секреты нарушат совместимость.

## Важные предупреждения
- `DB_PASSWORD`:
  - Устанавливается Postgres при первом старте контейнера.
  - Если нужно поменять позже — сделайте внутри БД: 
    - `docker exec -it diary_db psql -U diary_user -d diary_db -c "ALTER USER diary_user WITH PASSWORD 'новый_пароль';"`
    - Затем обновите `.env`.
  - Пересоздание тома `postgres_data` удаляет все данные.
- `SECRET_KEY` (Flask):
  - Смена ключа инвалидирует все текущие сессии.
  - Меняйте осознанно, предупреждая пользователей.

## Проверка после заполнения
- Бэкенд видит секреты:
  - Linux/macOS: `docker compose -f docker_compose_prod.yml exec backend printenv SECRET_KEY`
  - Windows: `docker compose -f docker_compose_prod.yml exec backend cmd /c set | findstr SECRET_KEY`
- Healthcheck API после запуска прод-стека: `curl -I https://diary.pw-new.club/api/health`

## Опционально: хранение `SECRET_KEY` в томе
Если не хотите хранить `SECRET_KEY` в `.env`, можно генерировать его при первом старте и сохранять в приватный том:
- Алгоритм:
  1) При запуске бэкенда: если `/app/data/secret_key` отсутствует — сгенерировать и записать; иначе читать.
  2) Использовать считанное значение как `SECRET_KEY` для приложения.
- Это безопаснее, чем впечатывать секрет в образ. При необходимости можно добавить init-скрипт.

## Полезные ссылки
- Python `secrets`: https://docs.python.org/3/library/secrets.html
- OpenSSL `rand`: https://www.openssl.org/docs/man3.0/man1/openssl-rand.html
- PowerShell/.NET `RandomNumberGenerator`: https://learn.microsoft.com/dotnet/api/system.security.cryptography.randomnumbergenerator
- Docker Compose — переменные окружения: https://docs.docker.com/compose/environment-variables/set-environment-variables/
- Docker Compose — `env_file`: https://docs.docker.com/compose/compose-file/#env_file
- Flask `SECRET_KEY` (конфиг): https://flask.palletsprojects.com/en/latest/config/#SECRET_KEY
- PostgreSQL `ALTER ROLE` (смена пароля): https://www.postgresql.org/docs/current/sql-alterrole.html
- Twelve-Factor App — конфигурация: https://12factor.net/ru/config