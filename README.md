# Currency Tracker

Сервис для отслеживания курсов валют с историческими данными.

## Содержимое репозитория

- `backend/` — сервис на Python (Litestar). Обрабатывает запросы, собирает и кеширует курсы валют, хранит историю и предоставляет REST API.
- `frontend/` — одностраничное приложение на React, отображает графики курсов валют.
- `docker-compose.yml` — запуск всех сервисов: Redis, `backend` и `frontend`.

## Основные фичи

- Получение текущих курсов относительно базовой валюты
- Запрос исторических котировок за N дней
- Встроенный фоновой прелоад исторических данных

## Быстрый старт (рекомендуется) — Docker Compose

Запускает все сервисы (Redis, Backend, Frontend) в контейнерах.

```bash
docker compose up --build
```

После успешного запуска:

- Backend: http://localhost:8000
- Frontend: http://localhost:3000

Docker Compose уже содержит healthcheck для Redis и Backend.

## Локальная разработка (без Docker)

Требуется `uv` и `Node.js`/`npm`.

Backend:

```bash
cd backend
uv sync --frozen
# Создайте файл `.env` в папке backend (см. ниже)
uv run -- uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Frontend:

```bash
cd frontend
npm install
npm start
```

## Переменные окружения

Создайте `.env` в директории `backend/` (пример минимальных переменных):

```env
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

Docker Compose подхватывает `.env` из корня проекта (если необходимо, поместите туда соответствующие переменные).
