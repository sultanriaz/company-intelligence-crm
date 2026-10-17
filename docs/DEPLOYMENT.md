# Deployment Guide

### 1. Docker Compose Production Topology

The platform deploys with Docker Compose running:
- `backend`: FastAPI API server (Uvicorn workers).
- `celery_worker`: Background agent and outbox task processor.
- `celery_beat`: Periodic scheduler for recrawls and maintenance.
- `frontend`: Nginx serving production Vite/React Single Page Application.
- `postgres`: PostgreSQL 16 database.
- `redis`: Redis 7.4 broker and state cache.

```bash
# Build and run all services
docker compose -f docker-compose.yml up --build -d
```

### 2. Manual Bare-Metal / Local Development Setup

#### Backend:
```bash
# In apps/backend
python -m venv .venv
source .venv/bin/activate  # or .\.venv\Scripts\Activate.ps1 on Windows
pip install -e .
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Celery Worker & Beat:
```bash
celery -A app.workers.celery_app.celery_app worker --loglevel=INFO -Q research,email,default
celery -A app.workers.celery_app.celery_app beat --loglevel=INFO
```

#### Frontend:
```bash
# In apps/frontend
npm install
npm run dev
```
