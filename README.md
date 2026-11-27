# TaskFlow API

[![CI](https://github.com/ZXCreatorDS/TaskFlow-API/actions/workflows/ci.yml/badge.svg)](https://github.com/ZXCreatorDS/TaskFlow-API/actions/workflows/ci.yml)

REST API для управления задачами команды: пользователи, проекты, метки, задачи и комментарии.

Стек: **Python 3.12 · FastAPI · PostgreSQL 16 · SQLAlchemy 2 · Alembic · Docker Compose**.

## Быстрый старт

```bash
cp .env.example .env
docker compose up --build
```

После старта:

- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- Health-check: http://localhost:8000/health

Проверка:

```bash
curl http://localhost:8000/health
# {"status":"ok"}
```

Остановка:

```bash
docker compose down
```

Данные PostgreSQL хранятся в именованном volume `pgdata` и сохраняются после
перезапуска контейнеров. Полностью удалить данные:

```bash
docker compose down -v
```

## Переменные окружения

Скопируйте `.env.example` в `.env` и при необходимости измените значения:

```env
POSTGRES_USER=taskflow
POSTGRES_PASSWORD=taskflow
POSTGRES_DB=taskflow
DATABASE_URL=postgresql+psycopg2://taskflow:taskflow@localhost:5432/taskflow

LOG_LEVEL=INFO
LOG_FORMAT="%(asctime)s %(levelname)s [%(name)s] %(message)s"
# LOG_FILE=logs/taskflow.log
```

В Docker переменная `DATABASE_URL` собирается автоматически и указывает на
хост `db`, а не на `localhost`. Файл `.env` в репозиторий не добавляется.

## Логирование

Логирование настраивается через переменные окружения:

| Переменная | Назначение | По умолчанию |
|---|---|---|
| `LOG_LEVEL` | `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` | `INFO` |
| `LOG_FORMAT` | формат сообщений | `%(asctime)s %(levelname)s [%(name)s] %(message)s` |
| `LOG_FILE` | путь к файлу логов (ротация 5 МБ, 3 файла) | не задан |

Используются все уровни:

- `DEBUG` — метод, путь и query-параметры каждого запроса;
- `INFO` — старт/остановка приложения, health-check, успешные запросы;
- `WARNING` — ответы `4xx`, `404`, конфликты `409`;
- `ERROR` — ответы `5xx`, недоступность БД в `/health`;
- `CRITICAL` — необработанное исключение в запросе.

Примеры запуска с разным уровнем:

```bash
LOG_LEVEL=DEBUG docker compose up --build
LOG_LEVEL=WARNING LOG_FILE=logs/taskflow.log docker compose up --build
```

В PowerShell:

```powershell
$env:LOG_LEVEL="DEBUG"
docker compose up --build
```

## Эндпоинты

Для каждого ресурса (`users`, `projects`, `labels`, `tasks`, `comments`)
доступны пять операций:

| Метод | URL | Ответ |
|---|---|---|
| `GET` | `/v1/{resource}` | `200`, список |
| `GET` | `/v1/{resource}/{id}` | `200` / `404` |
| `POST` | `/v1/{resource}` | `201`, созданная запись |
| `PATCH` | `/v1/{resource}/{id}` | `200`, частичное обновление |
| `DELETE` | `/v1/{resource}/{id}` | `204`, без тела |

Дополнительно:

- `GET /health` — проверка соединения с БД;
- `GET /v1/tasks?project_id=1&status=open` — фильтр задач;
- `GET /v1/comments?task_id=1` — фильтр комментариев;
- `GET /docs` — интерактивная документация.

Коды ошибок: `404` — запись не найдена, `422` — ошибка валидации,
`409` — дубликат уникального поля или нарушение внешнего ключа.

## Примеры запросов

### 1. Создать пользователя

```bash
curl -X POST http://localhost:8000/v1/users \
  -H "Content-Type: application/json" \
  -d '{"email":"ivan@example.com","display_name":"Иван Петров","role":"operator"}'
```

### 2. Создать проект и метку

```bash
curl -X POST http://localhost:8000/v1/projects \
  -H "Content-Type: application/json" \
  -d '{"name":"TaskFlow","description":"Основной проект"}'

curl -X POST http://localhost:8000/v1/labels \
  -H "Content-Type: application/json" \
  -d '{"name":"backend","color":"#2563eb"}'
```

### 3. Создать задачу

```bash
curl -X POST http://localhost:8000/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{"project_id":1,"assignee_id":1,"label_id":1,"title":"Сделать API","priority":"high"}'
```

### 4. Добавить комментарий

```bash
curl -X POST http://localhost:8000/v1/comments \
  -H "Content-Type: application/json" \
  -d '{"task_id":1,"author_id":1,"body":"Беру в работу"}'
```

### 5. Фильтры и обновление

```bash
curl "http://localhost:8000/v1/tasks?project_id=1&status=open"
curl "http://localhost:8000/v1/comments?task_id=1"

curl -X PATCH http://localhost:8000/v1/tasks/1 \
  -H "Content-Type: application/json" \
  -d '{"status":"done"}'
```

### 6. Каскадное удаление

```bash
curl -X DELETE http://localhost:8000/v1/projects/1
# 204 — задачи проекта и их комментарии тоже удалены
```

## CI

GitHub Actions workflow: `.github/workflows/ci.yml`. Пайплайн состоит из трёх
независимых джоб:

1. **Style** — `ruff format --check .`;
2. **Static analysis** — `ruff check .`;
3. **Tests** — `pytest -q`.

Локальный запуск тех же проверок:

```bash
pip install -r requirements-dev.txt
ruff format --check .
ruff check .
pytest -q
```

## Миграции

Схема создаётся только через Alembic, `Base.metadata.create_all()` не
используется. При старте контейнера `api` автоматически выполняется
`alembic upgrade head`.

Проверка миграций внутри контейнера:

```bash
docker compose exec api alembic upgrade head
docker compose exec api alembic downgrade base
docker compose exec api alembic upgrade head
```

Локальный запуск (при установленном PostgreSQL и Python 3.12):

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

## Структура проекта

```text
.
├── app/
│   ├── main.py          # FastAPI-приложение, /health и логирование запросов
│   ├── logging_config.py # настройка логов через env
│   ├── config.py        # настройки из переменных окружения
│   ├── database.py      # engine, SessionLocal, Base, get_db
│   ├── models.py        # SQLAlchemy-модели пяти таблиц
│   ├── schemas.py       # Pydantic-схемы запросов и ответов
│   └── routers/         # CRUD-роутеры по ресурсам
├── tests/
│   ├── conftest.py
│   └── test_api.py
├── .github/workflows/ci.yml
├── alembic/
│   ├── env.py
│   └── versions/0001_initial.py
├── alembic.ini
├── Dockerfile
├── docker-compose.yml
├── .dockerignore
├── .env.example
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
└── README.md
```

## Модель данных

- `users` — `email` уникален, роль `operator` или `admin`;
- `projects` — задачи проекта удаляются вместе с проектом;
- `labels` — уникальное имя, цвет в формате `#RRGGBB`;
- `tasks` — статусы `open` / `in_progress` / `done`, приоритеты
  `low` / `medium` / `high`; при удалении исполнителя или метки поля
  становятся `NULL`;
- `comments` — удаляются вместе с задачей; пользователя с комментариями
  удалить нельзя (API вернёт `409`).

Для `tasks.updated_at` в PostgreSQL создаётся триггер, поэтому поле
обновляется самой базой даже при изменении строки напрямую через SQL.

## Что не входит в задание

Авторизация, асинхронный SQLAlchemy, фронтенд, CD и Kubernetes не
реализуются. CI при этом добавлен отдельно.
