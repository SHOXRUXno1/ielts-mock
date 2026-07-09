# IELTS Mock

Платформа для пробных IELTS экзаменов: студенты сдают полные тесты (Listening, Reading, Writing, Speaking) и получают AI-оценку с band score и фидбеком.

## Структура

```
Mock/
├── backend/        FastAPI + SQLAlchemy 2.0 async + PostgreSQL
└── frontend/       React 19 + Vite + shadcn/ui + TanStack Router
```

## Стек

**Backend**
- Python 3.12, FastAPI, SQLAlchemy 2.0 (async, asyncpg)
- PostgreSQL 17, Alembic
- JWT + bcrypt
- Gemini 2.5 Flash-Lite (LLM-оценка Writing/Speaking)
- Groq Whisper (транскрипция Speaking)
- S3-совместимое хранилище Timeweb

**Frontend**
- React 19, TypeScript, Vite 8
- shadcn/ui, Tailwind CSS 4
- TanStack Router (file-based), TanStack Query
- Zustand (auth state)

## Запуск (локально)

### Backend
```powershell
cd backend
.\venv\Scripts\activate
$env:PYTHONPATH = "."
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

API: http://localhost:8000 · Swagger: http://localhost:8000/docs

### Frontend
```powershell
cd frontend
npm run dev
```

UI: http://localhost:5173

## Окружение

Скопируй `.env.example` в `.env` в каждом из `backend/` и `frontend/`, заполни ключи (Gemini, Groq, S3).
