# Environment Setup Guide

### 1. Prerequisites
- Python 3.11+
- Node.js 18+ and npm 9+
- Docker & Docker Compose (optional for local containerized run)
- PostgreSQL 16 & Redis 7

### 2. Environment Variables Configuration

Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Key environment configurations:
- `DATABASE_URL`: PostgreSQL connection string (`postgresql+asyncpg://...` or `postgresql://...` for sync).
- `REDIS_URL`: Redis broker string.
- `SECRET_KEY`: High-entropy 256-bit string for signing JWT tokens.
- `ENCRYPTION_KEY`: 32-byte key for AES-GCM credential encryption.
- `LLM_PROVIDER`: `mock` (for local offline dev), `openai`, or `anthropic`.
- `EMAIL_PROVIDER`: `mock` (for local dry run), `resend`, `sendgrid`, or `ses`.
- `EMAIL_DRY_RUN`: Set `true` to prevent actual outbound network calls.
- `EMAIL_REQUIRE_APPROVAL`: Set `true` to require human sign-off on all outbound emails.

### 3. Setting Up Local Python Environment
```bash
python -m venv .venv
source .venv/bin/activate # On Windows: .\.venv\Scripts\Activate.ps1
pip install -r apps/backend/requirements.txt
```

### 4. Running Migrations & Seeding Initial Data
```bash
cd apps/backend
alembic upgrade head
python scripts/seed_demo.py
```
