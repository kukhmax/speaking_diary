Телеграм‑бот для Speaking Diary

Кратко
- Бот открывает Speaking Diary как мини‑приложение (Telegram WebApp) и ведёт изолированные сессии для каждого пользователя.
- Реализация через вебхук Flask и прямые HTTP‑вызовы Telegram API (без фонового long‑polling процесса).

Где что лежит
- Сервис бота: `backend/services/telegram_bot.py`
- Роуты Flask (вебхук + эндпоинты сессий/заметок): `backend/routers/telegram.py`
- Пример переменных окружения: `.env.example`

Переменные окружения
- `TELEGRAM_BOT_TOKEN` — токен бота от @BotFather
- `PUBLIC_WEBAPP_URL` — публичный URL веб‑приложения (например, `https://diary.pw-new.club/`)
- `TELEGRAM_WEBHOOK_SECRET` — необязательный секрет для защиты вебхука (рекомендуется)
 - `WEBAPP_VERSION` — версия фронтенда для кеш‑бастинга Telegram WebView (рекомендуется). Если не указать, сервис добавит параметр `v=<номер_дня>` и версия будет меняться раз в сутки.

Что умеет
- `/start` — создаёт или восстанавливает сессию пользователя Telegram и отправляет кнопку «Открыть приложение» (Mini App). В URL мини‑аппа добавляется `?session=<token>`.
  Кроме того, добавляется параметр `v=<версия>` для обхода кеша Telegram.
- Персональные сессии — хранятся в `backend/data/telegram_sessions.json` (JSON), содержат `session_token`, `created_at`, `last_seen` и массив примерных `notes`. Сессии пользователей не пересекаются.
- Эндпоинты для заметок — `/api/telegram/notes` позволяют сохранять и получать простые заметки, привязанные к `session_token`.

Вебхук
- URL: `POST https://<ВАШ_ДОМЕН>/api/telegram/webhook?secret=<SECRET>`
- Тело: JSON‑объект Telegram Update.
- Ответ: `{ ok: true }` при успехе.

Проверка здоровья
- URL: `GET https://<ВАШ_ДОМЕН>/api/telegram/health`
- Ответ: `{ status: 'ok' }`.

Кнопка мини‑аппа
- При `/start` бот отправляет inline‑кнопку «Открыть приложение», которая открывает `PUBLIC_WEBAPP_URL` в Telegram как Mini App.
- Пример клавиатуры:
```
{
  "inline_keyboard": [[
    { "text": "Открыть приложение", "web_app": { "url": "https://diary.pw-new.club/?session=<token>&v=<version>" } }
  ]]
}
```

Настройка шаг за шагом
1) Создать бота в @BotFather
   - `/newbot` → задать имя и username → получить `TELEGRAM_BOT_TOKEN`.

2) Прописать переменные окружения
   - В `.env` указать:
     - `TELEGRAM_BOT_TOKEN=<вставьте токен>`
     - `PUBLIC_WEBAPP_URL=https://diary.pw-new.club/` (или ваш домен)
     - `TELEGRAM_WEBHOOK_SECRET=<случайная‑строка>`
     - `WEBAPP_VERSION=<например 2025-10-29>` — обновляйте при каждом релизе фронтенда, чтобы Telegram гарантированно загрузил свежую сборку.

     ```
     Что это

      - TELEGRAM_WEBHOOK_SECRET — это не токен от BotFather. Это ваша собственная секретная строка, чтобы защитить эндпоинт вебхука от посторонних запросов.
      - Вы придумываете и генерируете её сами (лучше криптографически случайную, длиной 32+ байта).
      Как сгенерировать

      - PowerShell (Windows):
        - python -c "import secrets; print(secrets.token_urlsafe(32))"
        - или [guid]::NewGuid().ToString('N') (проще, но менее случайно, всё же лучше вариант выше)
      - Node.js:
        - node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"
      - OpenSSL (Git Bash/WSL/Linux/macOS):
        - openssl rand -hex 32
      Возьмите полученное значение и запишите в .env :

      - TELEGRAM_WEBHOOK_SECRET=<ваша_случайная_строка>
      ```

3) Собрать/перезапустить бэкенд
   - Поднять бэкенд, чтобы он отдавал `/api/telegram/webhook` (Caddy уже проксирует `/api*` на backend):
     - `docker compose -f docker_compose.prod.yml up -d --build backend`

4) Зарегистрировать вебхук Telegram
   - URL вебхука: `https://diary.pw-new.club/api/telegram/webhook?secret=<SECRET>`
   - Вызвать Bot API:
     - Linux/macOS (Bash):
       - `export TELEGRAM_BOT_TOKEN="<ТОКЕН_ОТ_BOTFATHER>"`
       - `export TELEGRAM_WEBHOOK_SECRET="<ВАШ_СЕКРЕТ>"`
       - `curl -s "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/setWebhook?url=https://diary.pw-new.club/api/telegram/webhook?secret=${TELEGRAM_WEBHOOK_SECRET}"`
     - Windows PowerShell:
       - `$env:TELEGRAM_BOT_TOKEN = "<ТОКЕН_ОТ_BOTFATHER>"`
       - `$env:TELEGRAM_WEBHOOK_SECRET = "<ВАШ_СЕКРЕТ>"`
       - `curl.exe -s "https://api.telegram.org/bot$env:TELEGRAM_BOT_TOKEN/setWebhook?url=https://diary.pw-new.club/api/telegram/webhook?secret=$env:TELEGRAM_WEBHOOK_SECRET"`
       - Примечание: в PowerShell `curl` — алиас на `Invoke-WebRequest`. Используйте `curl.exe` или `Invoke-RestMethod`:
         - `$token = $env:TELEGRAM_BOT_TOKEN; $secret = $env:TELEGRAM_WEBHOOK_SECRET; $url = "https://api.telegram.org/bot$token/setWebhook?url=https://diary.pw-new.club/api/telegram/webhook?secret=$secret"`
         - `Invoke-RestMethod -Method Get -Uri $url`
   - Проверить:
     - Linux/macOS (Bash):
       - `curl -s "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getWebhookInfo" | jq`
     - Windows PowerShell:
       - `Invoke-RestMethod -Method Get -Uri "https://api.telegram.org/bot$env:TELEGRAM_BOT_TOKEN/getWebhookInfo"`
       - или `curl.exe -s "https://api.telegram.org/bot$env:TELEGRAM_BOT_TOKEN/getWebhookInfo" | ConvertFrom-Json`

5) Тестирование
   - Откройте бота в Telegram и отправьте `/start`.
   - Бот вернёт кнопку — нажмите, чтобы открыть мини‑приложение.
   - В URL будет `?session=<token>`. Фронтенд может передавать токен в запросах через заголовок `X-Session-Token` или параметр `?session=...`.

API заметок (пример)
- Создать заметку (в рамках сессии):
  - `POST /api/telegram/notes`
  - Заголовок: `X-Session-Token: <token>`
  - Тело: `{ "text": "hello" }`
  - Ответ: `{ "note": { id, text, timestamp } }`

- Получить заметки (в рамках сессии):
  - `GET /api/telegram/notes`
  - Заголовок: `X-Session-Token: <token>` (или `?session=<token>`)
  - Ответ: `{ "user_id": <tg_user_id>, "notes": [...] }`

Безопасность
- Используйте `TELEGRAM_WEBHOOK_SECRET`, чтобы ограничить доступ к вебхуку.
- Для продакшена рекомендуем валидировать `initData` из Telegram WebApp на бэкенде (см. https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app), чтобы надёжно связать пользователя и запросы мини‑аппа.

Продвинуто (опционально)
- Фронтенд в окружении Telegram может читать объект `Telegram.WebApp` и отправлять `initData` на бэкенд для проверки, вместо использования только параметра `session`.
- Для полноценного хранения данных используйте БД: добавьте `user_id` к вашим моделям и храните записи в таблицах.

Диагностика
- Если вебхук не вызывается, проверьте:
  - Вебхук URL публично доступен и возвращает 200.
  - Домен в `PUBLIC_WEBAPP_URL` корректен и открывается в Telegram.
  - Логи бэкенда: `docker logs diary_backend` — нет ли ошибок Flask.
  - `curl -I https://diary.pw-new.club/api/telegram/health` возвращает 200.




  =================================================================================

  Вот безопасный порядок действий, чтобы удалить старые контейнеры, образы и кэш Docker на вашем сервере.

Остановить стек

- Перейдите в директорию проекта (если вы уже в /opt/speaking_diary , пропустите):
  - cd /opt/speaking_diary
- Остановить и убрать контейнеры (сохранить данные БД):
  - docker-compose -f docker_compose.prod.yml down --remove-orphans
  - Альтернатива для Compose v2: docker compose -f docker_compose.prod.yml down --remove-orphans
- Если хочется удалить и связанные именованные тома (внимание: это удалит данные, например PostgreSQL):
  - docker-compose -f docker_compose.prod.yml down -v
  - Используйте только если точно не нужны данные.
Очистить неиспользуемое

- Общая очистка неиспользуемых контейнеров/образов/сетей/кэша:
  - docker system prune -a -f
- Очистить кэш билда (BuildKit и старый билд-кэш):
  - docker builder prune -a -f
- Дополнительно (если хотите по отдельности):
  - Удалить остановленные контейнеры: docker container prune -f
  - Удалить неиспользуемые образы: docker image prune -a -f
  - Удалить неиспользуемые сети: docker network prune -f
  - Удалить неиспользуемые тома: docker volume prune -f (будьте осторожны — удаляет данные)
Проверить результат

- Посмотреть, сколько места занято/освобождено:
  - docker system df
- Убедиться, что лишних образов нет:
  - docker images
- Убедиться, что нет лишних контейнеров:
  - docker ps -a
Пересобрать начисто

- Обновить и поднять продакшен заново:
  - docker-compose -f docker_compose.prod.yml up -d --build
- Если хотите полностью без использования кэша:
  - docker-compose -f docker_compose.prod.yml build --no-cache
  - docker-compose -f docker_compose.prod.yml up -d
- Для Compose v2 используйте docker compose в тех же командах.
Замечания

- Если у вас есть том для Postgres (например db ), не используйте down -v , чтобы не потерять данные. Проверьте раздел volumes: в docker_compose.prod.yml — там видно, какие тома созданы.
- Если образов много из-за частых сборок, периодически docker system prune -a и docker builder prune -a сильно помогают.
- После перезапуска проверьте статус:
  - docker ps
  - Логи: docker logs diary_backend и docker logs diary_caddy (имена сервисов смотрите в docker_compose.prod.yml ).