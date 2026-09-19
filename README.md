# Навигатор по мерам поддержки (subsidy-matcher-bot)

Чат-бот для платформы **МАХ**, который через серию из 3–4 уточняющих вопросов
(регион, форма бизнеса, отрасль, наличие сотрудников) подбирает предпринимателям,
фермерам и самозанятым доступные субсидии, гранты и льготы со ссылками на оформление.

> Направление хакатона: «Навигация по мерам поддержки для бизнеса и АПК».

## Стек

| Слой | Технологии |
| --- | --- |
| Язык | Python 3.11 |
| HTTP / коннектор API МАХ | `requests` |
| Webhook-сервер (production) | `FastAPI` + `uvicorn` |
| БД | PostgreSQL 15 (`SQLAlchemy` + `psycopg2`) |
| Состояния диалога (FSM) | Redis 7 (`redis-py`) |
| Развёртывание | Docker + Docker Compose |

## Архитектура

```
                       +---------------------------+
  Платформа МАХ        |  Бот (Python, src/)      |
  (platform-api2)      |                           |
     |                 |  max_client/  — коннектор |
     |  Update         |  handlers.py  — диспетчер |
     +---------------->|  main.py      — точка вх. |
  polling/webhook      |                           |
     ^                 |  (Роль 3) движок скоринга |
     |  send/answer    |  (Роль 4) FSM на Redis    |
     +-----------------+                           |
                       +----------+----------------+
                                  |
                    +-------------+-------------+
                    |             |             |
                 PostgreSQL     Redis       (webhook
                 (меры,         (состояния   :8000)
                  профили)       диалога)
```

**Модули (зоны ответственности):**

- `src/max_client/` — коннектор к API МАХ (Роль 1: Core API & DevOps).
- `src/config.py` — конфигурация из `.env` (Роль 1).
- `src/main.py`, `src/webhook.py` — точки входа: Long Polling и Webhook (Роль 1).
- `src/handlers.py` — диспетчер событий; шов для FSM и скоринга (Роли 3 и 4).
- БД и меры поддержки — добавляет Роль 2 (DB Architect).
- Скоринг и маршрутизация правил — Роль 3 (Rule Engine).
- Стейт-машина анкеты на Redis — Роль 4 (Bot Flow & FSM).

## Структура проекта

```
.
├── src/
│   ├── __init__.py
│   ├── config.py          # настройки из переменных окружения
│   ├── main.py            # входная точка (polling / webhook)
│   ├── webhook.py         # FastAPI-сервер для webhook-режима
│   ├── handlers.py        # диспетчер входящих событий
│   └── max_client/
│       ├── __init__.py
│       ├── client.py      # MaxClient (HTTP-методы API)
│       ├── models.py      # Update/Message/User/Button/клавиатура
│       └── errors.py      # исключения коннектора
├── Dockerfile
├── compose.yaml
├── requirements.txt
├── .env.example
└── README.md
```

## Контракт API МАХ (краткая шпаргалка)

- **Base URL:** `https://platform-api2.max.ru`
- **Авторизация:** заголовок `Authorization: <token>` (токен бота).
- **Отправка:** `POST /messages?user_id={id}` (или `?chat_id={id}`), тело — `NewMessageBody`:
  `text`, `attachments` (inline-клавиатура), `notify`, `format` (`markdown`/`html`).
- **Кнопки:** `attachments: [{type: "inline_keyboard", payload: {buttons: [[{type,text,payload|url}]]}}]`.
  Типы: `callback` (с `payload`), `link` (с `url`), `message`, `clipboard`, `request_contact`, `request_geo_location`, `open_app`.
- **Callback:** `POST /answers?callback_id={id}`; событие `message_callback` несёт `callback.callback_id`.
- **Получение событий (взаимоисключающие режимы):**
  - Long Polling — `GET /updates?marker=&limit=&timeout=&types=` → `{updates: Update[], marker}`.
  - Webhook — `POST /subscriptions` (`url`, `update_types`, `secret`); события приходят HTTPS POST
    с заголовком `X-Max-Bot-Api-Secret`.
- **Ограничения:** 30 rps на API; не более 2 сообщений/сек в один диалог.
- **События:** `bot_started`, `bot_added`, `message_created`, `message_callback`, `message_edited`,
  `message_removed`, `comment_*`, `user_added/removed` и др. (см. объект `Update`).

Полная документация: <https://dev.max.ru/docs-api>

## Переменные окружения

Скопируйте шаблон и заполните токен:

```bash
cp .env.example .env
# отредактируйте MAX_BOT_TOKEN и, при необходимости, остальные параметры
```

| Переменная | Назначение | По умолчанию |
| --- | --- | --- |
| `MAX_BOT_TOKEN` | Токен бота МАХ (обязателен) | — |
| `MAX_BASE_URL` | Базовый домен API | `https://platform-api2.max.ru` |
| `BOT_MODE` | `polling` или `webhook` | `polling` |
| `POLLING_TIMEOUT` / `POLLING_LIMIT` | Параметры long polling | `30` / `100` |
| `POLLING_EVENT_TYPES` | Типы событий через запятую (пусто = все) | — |
| `WEBHOOK_URL` / `WEBHOOK_SECRET` | Адрес и секрет webhook | — |
| `POSTGRES_USER/PASSWORD/DB/HOST/PORT` | Подключение к PostgreSQL | `myuser`/`mypassword`/`max_db`/`db`/`5432` |
| `REDIS_HOST` / `REDIS_PORT` | Подключение к Redis | `redis` / `6379` |

## Запуск

### Docker Compose (рекомендуется)

```bash
cp .env.example .env          # заполните MAX_BOT_TOKEN
docker compose up --build     # собрать и запустить bot + PostgreSQL + Redis
docker compose up -d --build  # то же в фоне
```

Сборка образа занимает **менее 5 минут** (тонкий базовый образ `python:3.11-slim`,
кэширование слоя с зависимостями, `.dockerignore`).

Проверка:

```bash
docker compose ps            # статус контейнеров (db/redis должны быть healthy)
docker compose logs -f bot   # логи бота
```

### Локально (без Docker, для разработки)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export MAX_BOT_TOKEN=...     # или создайте .env
python -m src.main           # BOT_MODE=polling по умолчанию
```

## Остановка

```bash
docker compose down          # остановить контейнеры
docker compose down -v       # остановить и удалить тома (данные БД/Redis)
```

## Порты

| Сервис | Порт | Назначение |
| --- | --- | --- |
| `bot` | `8000` | HTTP-сервер (только в режиме `BOT_MODE=webhook`) |
| `db` (PostgreSQL) | `5432` | БД мер поддержки и профилей |
| `redis` | `6379` | Состояния диалога (FSM) |

## Зависимости

Перечислены в [`requirements.txt`](requirements.txt): `requests`, `python-dotenv`,
`SQLAlchemy`, `psycopg2-binary`, `redis`, `fastapi`, `uvicorn`.

---

## Презентация — служебный слайд (Роль 1)

| Поле | Значение |
| --- | --- |
| Репозиторий (Git) | <https://github.com/ohhellgeez/subsidy-matcher-bot> |
| Ветка | `feature/core-api-devops` |
| Коммит | `0dd013588c32bf8c2c48c8d150dd1ee10eaf7661` |
| Токен бота | в `.env` → `MAX_BOT_TOKEN` (не публикуется в репозитории) |
| Базовый URL API | `https://platform-api2.max.ru` |
| Сборка | `docker compose up --build` (< 5 мин) |

