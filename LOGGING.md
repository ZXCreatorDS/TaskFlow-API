# Логирование в TaskFlow API

Краткий конспект по официальной документации Python
[`logging`](https://docs.python.org/3/library/logging.html) и
[Logging HOWTO](https://docs.python.org/3/howto/logging.html), а также
описание того, как логирование устроено в этом проекте.

## 1. Из чего состоит logging

`logging` — стандартная библиотека Python для регистрации событий.
Основные компоненты:

| Компонент | Задача |
|---|---|
| **Logger** | Интерфейс, который вызывает код: `logger.info(...)`, `logger.error(...)` |
| **Handler** | Куда отправить запись: консоль, файл, syslog, HTTP и т.д. |
| **Formatter** | Как выглядит строка лога: время, уровень, имя логгера, сообщение |
| **Filter** | Дополнительная фильтрация записей |
| **LogRecord** | Объект с данными одного события: сообщение, уровень, время, файл, строка |

Поток события:

```text
код -> Logger -> уровень логгера -> Handler -> Filter -> Formatter -> вывод
```

Логгеры образуют иерархию по именам через точку: `app`, `app.routers`,
`app.routers.users`. Дочерние логгеры по умолчанию передают записи
(propagate) обработчикам родителей — вплоть до корневого `root`.

## 2. Уровни логирования

| Уровень | Число | Когда использовать |
|---|---:|---|
| `NOTSET` | 0 | Не уровень сообщения, а режим «взять уровень родителя» |
| `DEBUG` | 10 | Диагностика: детали запроса, промежуточные значения |
| `INFO` | 20 | Подтверждение нормальной работы: старт, успешный запрос |
| `WARNING` | 30 | Неожиданно, но приложение продолжает работать: `404`, `409` |
| `ERROR` | 40 | Операция не выполнена: `5xx`, недоступна БД |
| `CRITICAL` | 50 | Приложение не может продолжать работу |

Если у логгера уровень `INFO`, то `DEBUG` игнорируется, а `INFO`,
`WARNING`, `ERROR`, `CRITICAL` проходят. По умолчанию у корневого
логгера уровень `WARNING`.

## 3. `logging` и `Logger`

Можно писать так:

```python
import logging
logging.warning("message")
```

Но функции модуля `logging` работают с **корневым** логгером. В больших
приложениях лучше создавать именованный логгер в каждом модуле:

```python
import logging

logger = logging.getLogger(__name__)
logger.info("user %s created", user_id)
```

Почему так:

- имя логгера совпадает с модулем, поэтому в логах видно источник;
- можно отдельно настроить уровень для `app.routers.tasks`;
- несколько вызовов `getLogger("app")` возвращают один и тот же объект;
- дочерние логгеры наследуют настройки и передают записи родителям.

Основные методы `Logger`:

- `debug()`, `info()`, `warning()`, `error()`, `critical()` — сообщение
  соответствующего уровня;
- `exception()` — `ERROR` + traceback, вызывать внутри `except`;
- `log(level, ...)` — произвольный уровень;
- `setLevel()` — порог;
- `addHandler()` / `removeHandler()` — обработчики;
- `addFilter()` — фильтры.

`logger.warning(...)` — правильное имя; `logger.warn(...)` устарел.

## 4. Настройка через переменные окружения

В проекте настройка вынесена в `app/logging_config.py`:

| Переменная | Значение по умолчанию | Назначение |
|---|---|---|
| `LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |
| `LOG_FORMAT` | `%(asctime)s %(levelname)s [%(name)s] %(message)s` | формат `logging.Formatter` |
| `LOG_FILE` | не задан | файл с ротацией (5 МБ, 3 файла) |

Примеры:

```bash
LOG_LEVEL=DEBUG docker compose up --build
LOG_LEVEL=WARNING LOG_FILE=logs/taskflow.log docker compose up --build
```

`configure_logging()`:

1. читает уровень из env и переводит его в число через
   `getattr(logging, level.upper(), logging.INFO)`;
2. очищает старые обработчики;
3. добавляет `StreamHandler` для консоли;
4. при заданном `LOG_FILE` добавляет `RotatingFileHandler`;
5. приглушает `uvicorn.access`, чтобы не дублировать запросы.

## 5. Все уровни в проекте

Уровни используются в реальных сценариях:

- `DEBUG` — `app/main.py`, middleware: метод, путь и query запроса;
- `INFO` — старт/остановка, health-check, успешные HTTP-запросы;
- `WARNING` — `app/routers/common.py`: `404` и конфликты `409`;
- `ERROR` — `app/main.py`: `5xx` и недоступность БД в `/health`;
- `CRITICAL` — `app/main.py`: необработанное исключение в middleware.

Отдельная демонстрация всех пяти уровней:

```bash
# локально
python -m app.logging_demo

# в запущенном контейнере — все пять уровней
docker compose exec -e LOG_LEVEL=DEBUG api python -m app.logging_demo
```

Ожидаемый вывод:

```text
DEBUG [taskflow.logging_demo] DEBUG: detailed diagnostic information
INFO [taskflow.logging_demo] INFO: normal application event
WARNING [taskflow.logging_demo] WARNING: unexpected but recoverable situation
ERROR [taskflow.logging_demo] ERROR: operation failed
CRITICAL [taskflow.logging_demo] CRITICAL: application cannot continue
```

Проверить, что уровень управляется через env:

```bash
LOG_LEVEL=WARNING python -m app.logging_demo
```

Будут только `WARNING`, `ERROR`, `CRITICAL`.

## 6. Практики, которые стоит запомнить

1. В каждом модуле — `logger = logging.getLogger(__name__)`.
2. Не использовать `print()` для диагностики.
3. Передавать данные лениво: `logger.info("user %s", user_id)`, а не
   `logger.info(f"user {user_id}")`.
4. Для исключений — `logger.exception(...)` или `exc_info=True`, чтобы
   был traceback.
5. Не логировать пароли, токены, `DATABASE_URL` с паролем.
6. Настраивать логирование один раз при старте приложения.
7. Библиотеки не должны сами добавлять обработчики — только приложение
   решает, куда и как писать логи.
8. Уровни — это контракт: `ERROR` не заменяет `WARNING`, а `DEBUG` не
   должен быть единственным уровнем.

## 7. Ссылки

- [`logging` — API reference](https://docs.python.org/3/library/logging.html)
- [Logging HOWTO](https://docs.python.org/3/howto/logging.html)
- [Logging Cookbook](https://docs.python.org/3/howto/logging-cookbook.html)
- [`logging.config`](https://docs.python.org/3/library/logging.config.html)
- [`logging.handlers`](https://docs.python.org/3/library/logging.handlers.html)
