# Путевые листы пассажирского транспорта

Веб-приложение для диспетчерской автобусного предприятия: справочники водителей, автобусов, маршрутов и выпусков, месячные графики, ежедневные наряды, автоматическая выписка путевых листов, журнал сквозной нумерации, топливо, пробег и отчеты.

## Состав

- `backend` - FastAPI, SQLAlchemy, Alembic-ready структура, Excel/PDF export endpoints.
- `frontend` - React + TypeScript + Ant Design.
- `docker-compose.yml` - PostgreSQL, Redis, backend, frontend.
- `templates` - место для Excel/PDF шаблонов организации.

## Быстрый запуск через Docker

```bash
docker compose up --build
```

После запуска:

- Frontend: http://localhost:5180
- API: http://localhost:8000
- Swagger: http://localhost:8000/docs

## Локальный запуск backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Локальный запуск frontend

```bash
cd frontend
npm install
npm run dev
```

## Что реализовано в MVP

- Справочники водителей, автобусов, маршрутов, выпусков.
- Наряд на день с проверками конфликтов документов, транспорта и водителей.
- Автоматическое создание путевых листов из наряда.
- Сквозная нумерация формата `ПЛ-2026-000001`.
- Закрытие путевого листа с расчетом пробега и фактического расхода топлива.
- Журнал путевых листов с фильтрами на API.
- Экспорт наряда, журнала и путевого листа в Excel.
- Печатная HTML-форма путевого листа по структуре образца.
- Заготовки ролей, JWT, Celery, Redis и PostgreSQL в конфигурации.
