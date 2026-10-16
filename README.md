# Сервис сбора цен криптовалют

Сервис, который собирает цены на BTC и ETH индексы с биржи Deribit каждую минуту, сохраняет их в PostgreSQL базу данных и предоставляет REST API для получения этих данных через FastAPI.

## Стек технологий

- Python 3.14
- FastAPI и Pydantic Settings
- SQLAlchemy 2.x с asyncpg
- PostgreSQL и Alembic для миграций
- aiohttp для HTTP-запросов к Deribit API
- Celery Beat / Worker с RabbitMQ в качестве брокера
- uv, Ruff, mypy, pytest, pre-commit, Docker Compose и GitLab CI

## Архитектура

```text
Deribit public/get_index_price
             |
       aiohttp client
             |
   Celery Beat -> RabbitMQ -> Celery Worker
                            |
                      collection service
                            |
                    repository / SQLAlchemy
                            |
                        PostgreSQL
                            ^
                       FastAPI API
```

- `clients` - модуль для внешнего HTTP-доступа к Deribit API
- `services` - реализация бизнес-логики приложения  
- `repositories` - работа с базой данных через SQLAlchemy
- `api` - валидация HTTP входных параметров и сериализация ответов
- Задачи Celery - тонкая обертка вокруг процесса сбора данных

## Пошаговое разворачивание

### 1. Клонирование репозитория

```bash
git clone <url-репозитория>
cd crypto-price-service
```

### 2. Создание конфигурационного файла

Создайте файл `.env` на основе примера:

```bash
cp .env.example .env
```

### 3. Установка зависимостей

Установите все зависимости с помощью uv:

```bash
uv sync --all-groups
```

### 4. Применение миграций базы данных

```bash
uv run alembic upgrade head
```

### 5. Запуск сервиса

Для запуска в локальной среде:

1. Запустите PostgreSQL и Redis (можно использовать Docker Compose):

```bash
docker compose up -d postgres redis
```

2. Запустите API:

```bash
make run
```

3. В отдельных терминалах запустите Celery Worker и Beat:

```bash
make run.worker
make run.beat
```

### 6. Использование Docker Compose

Для запуска через Docker Compose:

```bash
cp .env.example .env
docker compose up --build -d
docker compose exec api uv run --no-sync alembic upgrade head
```

После запуска:
- API доступен по адресу: http://localhost:8000
- Swagger UI: http://localhost:8000/docs  
- ReDoc: http://localhost:8000/redoc
- Health endpoint: http://localhost:8000/health

Остановка сервисов:
```bash
make docker-down
```

Данные PostgreSQL хранятся в именованном Docker volume. Для полного удаления данных используйте:
```bash
docker compose down -v
```

## API

Все эндпоинты требуют обязательный query-параметр `ticker` со значениями `btc_usd` или `eth_usd`.

### Получение всех сохраненных данных по указанной валюте

```bash
curl 'http://localhost:8000/api/v1/prices?ticker=btc_usd&offset=0&limit=100'
```

Возвращает записи, упорядоченные по времени в порядке возрастания. Используйте `offset` и `limit` для пагинации.

### Получение последней цены валюты

```bash
curl 'http://localhost:8000/api/v1/prices/latest?ticker=eth_usd'
```

Возвращает HTTP 404, если нет сохраненных данных для указанной валюты.

### Получение цены валюты с фильтром по дате

```bash
curl 'http://localhost:8000/api/v1/prices/history?ticker=btc_usd&from_timestamp=1800000000&to_timestamp=1800003600'
```

Параметры `from_timestamp` и `to_timestamp` - необязательные, включают границы UNIX timestamp в секундах. Если нижняя граница больше верхней, возвращает HTTP 422.

Пример ответа:

```json
{
  "id": 1,
  "ticker": "btc_usd",
  "price": "65000.2500000000",
  "timestamp": 1800000000
}
```

## Миграции базы данных

Применение миграций:

```bash
make migrate
```

Генерация новой миграции после изменений в моделях:

```bash
make migration message="описание изменений"
```

Перед коммитом проверяйте автогенерируемые миграции на соответствие. Проверка дрифта модели:

```bash
make migration-check
```

## Контроль качества и тесты

Установка pre-commit хуков:

```bash
make pre-commit-install
```

Запуск всех проверок:

```bash
make pre-commit
```

Основные команды:

```bash
make format          # Форматирование кода
make lint            # Линтинг
make check           # Проверка типов
make test            # Запуск всех тестов
make test-unit       # Запуск unit-тестов
make test-integration # Запуск integration-тестов
```

## Конфигурация

См. `.env.example`. Важные настройки:

- `DATABASE_URL` — URL подключения к PostgreSQL базе данных
- `REDIS_URL` — URL бэкенда Celery (Redis)
- `DERIBIT_BASE_URL` — базовый URL Deribit API v2
- `DERIBIT_TIMEOUT_SECONDS` — таймаут HTTP запросов
- `PRICE_COLLECTION_INTERVAL_SECONDS` — интервал сбора данных (по умолчанию 60 секунд)
- `COLLECTION_RETRY_ATTEMPTS` и `COLLECTION_RETRY_DELAY_SECONDS` — настройки повторных попыток

Не коммитьте `.env` файл и реальные учетные данные.

## Design decisions

### Выбор индекса цены

Сервис использует `public/get_index_price` метод Deribit API с параметрами `index_name=btc_usd` и `index_name=eth_usd`. Не используются цены последней сделки или фьючерсов. Для этого публичного эндпоинта не требуется API ключ.

### Точность цены

Цены представлены как `Decimal` и сохраняются в PostgreSQL как `NUMERIC(30, 10)` для избежания ошибок хранения с плавающей точкой.

### Временная метка

`timestamp` - UNIX timestamp в секундах, захватывается сборщиком сразу после получения цены. Это время сбора, а не время события на бирже.

### Планирование задач

Celery Beat отвечает за периодическое выполнение задач, Celery Worker - за их выполнение. В одном развертывании запускается только один экземпляр Beat, чтобы избежать дублирования задач.

### Брокер

RabbitMQ используется в качестве брокера, так как он подходит для этой задачи и соответствует стеку проекта. Redis используется в качестве бэкенда для хранения результатов задач Celery.

### Изоляция ошибок

BTC и ETH собираются независимо, поэтому ошибка при сборе одного индекса не мешает сохранению другого. Ошибки на уровне тикера логируются. Неожиданные ошибки на уровне задачи используют ограниченные повторные попытки Celery.

### Доступ к базе данных

Сессии SQLAlchemy асинхронные и ограничены отдельными операциями. Alembic отвечает за изменения схемы, приложение не создает таблицы автоматически.

### Пагинация API

Эндпоинт истории поддерживает `offset` и `limit` для ограничения размера ответов. По умолчанию лимит 100, максимальный 1000. Клиенты могут странично получать все сохраненные наблюдения.

### Валидация

Значения ticker ограничены двумя запрашиваемыми индексами. Фильтры по времени включают границы.

### Объем функциональности

Аутентификация, публичные эндпоинты записи и управление секретами в продакшене находятся вне области задачи.

## Известные ограничения

- API доступен только для чтения и не требует аутентификации, как указано в задании.
- Эндпоинт полной истории пагинирован для защиты памяти и размера ответа.
- Точная совместимость должна быть проверена в целевой среде после установки зависимостей. CI настроен на Python 3.14.
- Продакшен развертывания должны добавить метрики, уведомления, аутентификацию/ограничение скорости там, где это необходимо, и координированную миграцию данных.

## Требования

- Python 3.14
- [uv](https://docs.astral.sh/uv/)
- Docker и Docker Compose для контейнеризованного запуска
