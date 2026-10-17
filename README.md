# Enterprise AI Multi-Agent Company Intelligence, CRM & Outreach Automation Platform

[![CI Pipeline](https://github.com/organization/company-intelligence-crm/actions/workflows/ci.yml/badge.svg)](https://github.com/organization/company-intelligence-crm/actions/workflows/ci.yml)
[![Python Version](https://img.shields.io/badge/python-3.11%20%7C%203.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.3+-61DAFB.svg)](https://react.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An enterprise-grade, production-hardened multi-agent platform designed to discover companies, crawl and parse corporate websites with defense-in-depth web scrapers, synthesize company intelligence, automatically qualify sales leads, manage relationships via a custom CRM, and execute compliant, personalized outbound email campaigns with human-in-the-loop review and transactional outbox guarantees.

---

## Table of Contents

- [1. Architectural Overview](#1-architectural-overview)
- [2. Multi-Agent System Design](#2-multi-agent-system-design)
  - [Workflow State Machine](#workflow-state-machine)
  - [The 11 Specialist Agents](#the-11-specialist-agents)
- [3. Defense-in-Depth & Security](#3-defense-in-depth--security)
  - [Anti-SSRF Web Security](#anti-ssrf-web-security)
  - [Prompt Injection Quarantine](#prompt-injection-quarantine)
  - [Transactional Outbox & Idempotency](#transactional-outbox--idempotency)
  - [Cryptographic Safeguards](#cryptographic-safeguards)
- [4. Technology Stack](#4-technology-stack)
- [5. Repository Structure](#5-repository-structure)
- [6. Getting Started](#6-getting-started)
  - [Prerequisites](#prerequisites)
  - [Option A: Docker Compose (Recommended)](#option-a-docker-compose-recommended)
  - [Option B: Local Bare-Metal Setup](#option-b-local-bare-metal-setup)
- [7. Seeding & Demo Data](#7-seeding--demo-data)
- [8. Multi-Agent Outreach Workflow](#8-multi-agent-outreach-workflow)
- [9. REST API Catalog](#9-rest-api-catalog)
- [10. Testing & Verification](#10-testing--verification)
- [11. Operations & Observability](#11-operations--observability)
- [12. Comprehensive Documentation Index](#12-comprehensive-documentation-index)

---

## 1. Architectural Overview

```
                          ┌───────────────────────────┐
                          │    ENTERPRISE USER / UI   │
                          └─────────────┬─────────────┘
                                        │ HTTPS / JWT
                                        ▼
                          ┌───────────────────────────┐
                          │   FASTAPI API GATEWAY     │
                          │   (Auth, RBAC, Auditing)  │
                          └─────────────┬─────────────┘
                                        │
           ┌────────────────────────────┼────────────────────────────┐
           ▼                            ▼                            ▼
┌─────────────────────┐      ┌─────────────────────┐      ┌─────────────────────┐
│  ORCHESTRATION HUB  │      │  CUSTOM CRM ENGINE  │      │ TRANSACTIONAL OUTBOX│
│ (State Machine,     │      │ (Pipelines, Stages, │      │ (Idempotency, Gate, │
│  Budget, Execution) │      │  Leads, Contacts)   │      │  Suppression, ESP)  │
└──────────┬──────────┘      └──────────┬──────────┘      └──────────┬──────────┘
           │                            │                            │
           ▼                            ▼                            ▼
┌───────────────────────────────────────────────────────────────────────────────┐
│                    POSTGRESQL 16 / SQLALCHEMY 2.X ASYNC                       │
│    (30 Multi-Tenant Schema Entities, JSONB Checkpoints, Append-Only Audits)   │
└───────────────────────────────────────┬───────────────────────────────────────┘
                                        │
                                        ▼
┌───────────────────────────────────────────────────────────────────────────────┐
│                            CELERY WORKERS + REDIS                             │
│       (Distributed Crawling, LLM Orchestration, Scheduled In-Process Beat)   │
└───────────────────────────────────────────────────────────────────────────────┘
```

The platform strictly separates **probabilistic LLM reasoning** from **deterministic application logic**:
- **Deterministic Code Ownership:** State machine progression, database transactions, SSRF protection filters, token bucket rate limits, budget enforcement, email compliance checks, approval gates, and network outbox delivery are governed 100% by deterministic Python code.
- **AI Agent Contracts:** Specialist agents operate behind strictly typed Pydantic V2 schemas with JSON schema enforcement, defensive sanitation wrappers, and fallback heuristics for resilient offline execution.

---

## 2. Multi-Agent System Design

### Workflow State Machine

The research and outreach pipeline transitions deterministically through 12 formal states:

```
[CREATED] ──► [VALIDATING] ──► [DISCOVERING] ──► [EXTRACTING] ──► [RESEARCHING]
                                                                        │
[EMAIL_PREPARATION] ◄── [SAVING] ◄── [ANALYZING] ◄── [VERIFYING] ◄──────┘
        │
        ▼
[APPROVAL_PENDING] ──► [SENDING] ──► [COMPLETED]
        │
        └─── (Rejected) ──► [CANCELLED] / [FAILED]
```

### The 11 Specialist Agents

| Agent | Module | Responsibility | Safety & Governance |
|---|---|---|---|
| **1. Supervisor Agent** | `supervisor.py` | Decomposes goals, manages execution plans, enforces budget ($2.00 max, 300s timeout), commits checkpoints. | Non-LLM state machine governs transitions; halts if budget depleted. |
| **2. Discovery Agent** | `discovery.py` | Discovers seed domain pages (About, Products, Contact, Careers, News) up to max crawl depth. | URL normalization, scope boundary enforcement, duplicate rejection. |
| **3. Web Scraping Agent** | `scraping.py` | Fetches static HTML (HTTPX) or dynamic JS (Playwright) content; extracts raw text, metadata, contacts. | Pre-flight DNS SSRF check, robots.txt cache, per-domain token bucket. |
| **4. Research Agent** | `research.py` | Extracts industry, offerings, tech stack, funding signals, pain points, and corporate profiles. | Prompt injection quarantine; refuses ungrounded speculation. |
| **5. Verification Agent** | `verification.py` | Cross-references extracted facts against source text; computes confidence scores and flags contradictions. | Rejects facts with confidence < 0.60; tags discrepancies. |
| **6. Insights Agent** | `insights.py` | Generates executive summaries, ICP fit analysis, business SWOT, and outreach angle suggestions. | Constrained strictly to verified facts; produces structured JSON. |
| **7. Qualification Agent**| `qualification.py` | Evaluates configurable qualification rules (revenue, headcount, tech fit) to assign 0-100 scores. | Deterministic rule weighting combined with explainable reasoning. |
| **8. CRM Sync Agent** | `crm_sync.py` | Upserts Company, Contacts, and Lead records; moves qualified leads to active CRM pipeline stages. | Workspace tenancy isolation; deduplicates contacts by normalized email. |
| **9. Email Drafting Agent**| `email_draft.py` | Drafts personalized, multi-touch cold outreach emails referencing verified company pain points. | Injects CAN-SPAM physical address & mandatory unsubscribe tokens. |
| **10. Delivery Agent** | `email_delivery.py`| Processes Transactional Outbox; executes delivery via Mock, Resend, SendGrid, or Amazon SES. | Idempotency key (SHA-256) check; suppresses unapproved drafts. |
| **11. Tracking Agent** | `email_tracking.py`| Ingests delivery, open, click, bounce, and complaint webhooks; updates recipient metrics. | HMAC-SHA256 signature verification; auto-suppresses bounces. |

---

## 3. Defense-in-Depth & Security

### Anti-SSRF Web Security
Every outbound network crawl request initiated by the crawler undergoes multi-stage verification (`app/security/ssrf.py`):
1. **Pre-flight DNS Resolution:** Resolves hostname to all target IPs before connection.
2. **CIDR Blacklist Checking:** Blocks RFC 1918 private subnets (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), loopback (`127.0.0.0/8`), link-local (`169.254.0.0/16`), multicast (`224.0.0.0/4`), broadcast (`255.255.255.255`), IPv6 loopback (`::1`), and cloud metadata services (`169.254.169.254`, `metadata.google.internal`).
3. **Per-Redirect Event Hooks:** Custom HTTPX redirect transport hooks re-verify each subsequent redirect URL against the SSRF filter, thwarting DNS rebinding and open redirect vulnerabilities.

### Prompt Injection Quarantine
Scraped untrusted text is processed through defensive filters (`app/security/prompt_guard.py`):
- Regular expression heuristics detect common jailbreak patterns, system prompt overrides (`ignore previous instructions`, `system prompt:`), and delimiter injection attacks.
- Scraped content is isolated within sanitized XML delimiters (`<untrusted_scraped_content>...</untrusted_scraped_content>`) before presentation to LLMs, neutralizing prompt escaping vectors.

### Transactional Outbox & Idempotency
Outbound communications implement the Transactional Outbox pattern (`app/email/outbox.py`):
- Email messages are committed to the relational database inside the business transaction with status `PENDING`.
- Double-send protection is guaranteed via a deterministic SHA-256 idempotency key generated from `(campaign_id, recipient_email, template_id, touchpoint_number)`.
- If an email has already been sent or is currently inflight, duplicate executions are aborted instantly with zero risk of duplicate external API calls.

### Cryptographic Safeguards
- **Tenant API Keys:** Third-party provider credentials (Resend, SendGrid, AWS SES) are encrypted at rest using authenticated **AES-256-GCM** with unique 96-bit initialization vectors (`app/security/crypto.py`).
- **Webhook Authentication:** Webhooks require **HMAC-SHA256** signature verification using per-workspace shared secrets.
- **Passwords:** Passwords are hashed using native **Bcrypt** with dynamic salting.

---

## 4. Technology Stack

| Domain | Technology | Description |
|---|---|---|
| **Backend Core** | Python 3.11+ / FastAPI | High-performance asynchronous REST API framework. |
| **Agent Framework**| Custom State Machine + CrewAI | Deterministic orchestrator with pluggable LLM adapters (Mock, OpenAI, Anthropic). |
| **Database & ORM** | PostgreSQL 16 / SQLAlchemy 2.x | Async ORM (`asyncpg` / `aiosqlite`), `lazy="selectin"` relationship eager loading. |
| **Migrations** | Alembic | Version-controlled declarative schema migrations across 30 entities. |
| **Web Crawling** | HTTPX + BeautifulSoup4 + Playwright | Non-blocking HTTP crawler with headless browser dynamic JS fallback. |
| **Task Queue** | Celery + Redis | Asynchronous distributed background task execution and job scheduling. |
| **Email Adapters** | Resend, SendGrid, Amazon SES, Mock | Pluggable email delivery engine with dry-run and compliance safeguards. |
| **Frontend UI** | React 18 + TypeScript + Tailwind CSS | Single Page Application dashboard with Lucide icons and Vite tooling. |
| **Testing** | Pytest + Pytest-Asyncio + Pytest-Cov | Hermetic unit, integration, and E2E acceptance test coverage. |

---

## 5. Repository Structure

```
.
├── .github/workflows/ci.yml           # Automated CI workflow (linting, tests, build)
├── docker-compose.yml                 # Multi-container orchestration (DB, Redis, App, Workers)
├── pytest.ini                         # Root Pytest runner configuration
├── .env.example                       # Documented environment variables template
├── docs/                              # 14 Full System Architecture & Engineering Artifacts
│   ├── PRD.md                         # Product Requirements Document
│   ├── HLD.md                         # High-Level Architecture Design
│   ├── LLD.md                         # Low-Level Component Design
│   ├── DATABASE.md                    # Data Dictionary & Schema Specification
│   ├── AGENT_ARCHITECTURE.md          # Multi-Agent Specification & Safety Gates
│   ├── WORKFLOW_DIAGRAMS.md           # Sequence & State Machine Diagrams
│   ├── API.md                         # REST API Specification (OpenAPI compliant)
│   ├── SECURITY.md                    # Threat Model & Anti-SSRF Architecture
│   ├── EMAIL_COMPLIANCE.md            # CAN-SPAM, GDPR, Suppression & Deliverability
│   ├── DEPLOYMENT.md                  # Docker & Cloud Production Deployment Guide
│   ├── TESTING.md                     # Test Plan, Fixtures, Acceptance Strategy
│   ├── OPERATIONS.md                  # Runbooks, Monitoring, Incident Response
│   ├── ENVIRONMENT_SETUP.md           # Bare-Metal & Container Setup Instructions
│   ├── TROUBLESHOOTING.md             # Common Issues & Resolution Matrix
│   └── TRACEABILITY_MATRIX.md         # Requirements-to-Implementation Mapping
├── apps/
│   ├── backend/
│   │   ├── app/
│   │   │   ├── api/v1/                # 15 FastAPI Route Modules
│   │   │   ├── agents/                # 11 Specialist Agents + LLM Adapters
│   │   │   ├── core/                  # Security, Database, Config, Logging
│   │   │   ├── email/                 # Outbox, Compliance, Template Engine, Providers
│   │   │   ├── models/                # 30 SQLAlchemy Relational Entities
│   │   │   ├── orchestration/         # Workflow Engine & State Machine
│   │   │   ├── repositories/          # Domain Data Access Repositories
│   │   │   ├── schemas/               # Pydantic V2 Request/Response/Contracts
│   │   │   ├── scraping/              # HTTPX Crawler, Robots Parser, Rate Limiter
│   │   │   ├── security/              # SSRF Checker, Prompt Guard, AES-GCM
│   │   │   └── workers/               # Celery Tasks & In-Process Scheduler
│   │   ├── migrations/                # Alembic Schema Migrations
│   │   └── tests/                     # Unit, Integration, and Acceptance Tests
│   └── frontend/
│       ├── src/
│       │   ├── api/                   # Typed Axios API Client
│       │   ├── components/            # Reusable UI Components (Sidebar, Header, etc.)
│       │   ├── pages/                 # 10 Full Feature Pages (Dashboard, Pipeline, etc.)
│       │   └── types/                 # Shared TypeScript Type Definitions
│       ├── package.json               # Frontend Dependencies & Scripts
│       └── vite.config.ts             # Vite + Tailwind Build Pipeline
└── scripts/
    └── seed_demo.py                   # Complete Demo Seeder Script
```

---

## 6. Getting Started

### Prerequisites
- **Git**
- **Docker & Docker Compose** (for containerized deployment)
- *Or for local bare-metal:* **Python 3.11+**, **Node.js 18+**, **PostgreSQL 16**, **Redis 7**

---

### Option A: Docker Compose (Recommended)

1. **Clone the repository and prepare environment:**
   ```bash
   cp .env.example .env
   ```

2. **Launch all services:**
   ```bash
   docker compose up --build -d
   ```

3. **Verify running containers:**
   ```bash
   docker compose ps
   ```

4. **Access the application:**
   - **Frontend CRM UI:** [http://localhost:3000](http://localhost:3000)
   - **Backend API Docs (Swagger):** [http://localhost:8000/docs](http://localhost:8000/docs)
   - **Backend Health Check:** [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)

---

### Option B: Local Bare-Metal Setup

#### 1. Backend Setup

```bash
# Create and activate Python virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r apps/backend/requirements.txt
pip install email-validator pytest-cov

# Configure environment
cp .env.example .env

# Run database migrations
cd apps/backend
alembic upgrade head
cd ../..

# Seed demo data
python scripts/seed_demo.py

# Start FastAPI development server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --app-dir apps/backend
```

#### 2. Frontend Setup

```bash
cd apps/frontend

# Install Node modules
npm install

# Start Vite development server
npm run dev
```

The frontend will start at [http://localhost:5173](http://localhost:5173) with automatic proxying to the backend API at `http://localhost:8000`.

---

## 7. Seeding & Demo Data

The platform comes with a turnkey seed script (`scripts/seed_demo.py`) that initializes a rich multi-tenant environment:
- **Default Organization:** `Acme Global Enterprises`
- **Default Admin Account:** `admin@acme.local` (Password: `AdminPassword123!`)
- **Default Member Account:** `sales@acme.local` (Password: `SalesPassword123!`)
- **Configured Pipeline:** Standard 5-stage B2B Sales Pipeline (*Lead In, Contacted, Qualified, Demo Scheduled, Closed Won*)
- **Target Companies:** Pre-populated profiles (*Stripe, Shopify, Linear, Datadog*) with verified facts, contacts, and lead scores.
- **Outreach Campaigns:** Pre-configured campaign with CAN-SPAM compliant Jinja2 email templates.

Run the seeder at any time:
```bash
python scripts/seed_demo.py
```

---

## 8. Multi-Agent Outreach Workflow

### Running a Complete Research & Outreach Run

1. **Trigger via REST API:**
   ```bash
   curl -X POST http://localhost:8000/api/v1/research/start \
     -H "Authorization: Bearer <YOUR_ACCESS_TOKEN>" \
     -H "Content-Type: application/json" \
     -d '{
       "company_id": "c0000000-0000-0000-0000-000000000001",
       "allowed_domains": ["stripe.com"],
       "max_crawl_depth": 2,
       "max_pages": 10,
       "research_goals": ["Extract core APIs", "Identify enterprise sales pain points"],
       "auto_qualify": true,
       "auto_prepare_email": true
     }'
   ```

2. **Monitor Execution:**
   - Watch the agent state machine progress in real-time on the **Research Console** UI (`/research`).
   - Observe live checkpoint transitions: `DISCOVERING` ➔ `EXTRACTING` ➔ `RESEARCHING` ➔ `VERIFYING` ➔ `ANALYZING` ➔ `SAVING` ➔ `EMAIL_PREPARATION`.

3. **Human Review Gate:**
   - When `EMAIL_REQUIRE_APPROVAL=true` (default), newly drafted emails are placed in `APPROVAL_PENDING`.
   - Team members inspect drafted emails, verified facts, and recipient scores in the **Approval Queue** UI (`/approvals`).
   - One-click approval commits the message to the **Transactional Outbox** for delivery.

---

## 9. REST API Catalog

The platform provides a comprehensive OpenAPI v3 documented REST API:

| Prefix | Endpoint | Method | Description |
|---|---|---|---|
| `/api/v1/auth` | `/login`, `/register`, `/me` | `POST`, `GET` | JWT authentication and session management. |
| `/api/v1/companies` | `/`, `/{id}`, `/{id}/enrich` | `GET`, `POST`, `PUT` | Company intelligence catalog and discovery records. |
| `/api/v1/contacts` | `/`, `/{id}` | `GET`, `POST`, `DELETE`| Discovered corporate contact directory. |
| `/api/v1/research` | `/start`, `/{id}/status`, `/{id}` | `POST`, `GET` | Autonomous agent execution lifecycle management. |
| `/api/v1/agents` | `/status`, `/budget` | `GET` | Agent health, metrics, and budget telemetry. |
| `/api/v1/leads` | `/`, `/{id}/score`, `/{id}/qualify` | `GET`, `POST` | Lead scoring, breakdown rules, and stage movement. |
| `/api/v1/pipelines` | `/`, `/{id}/stages` | `GET`, `POST` | CRM pipeline stages and Kanban state management. |
| `/api/v1/campaigns` | `/`, `/{id}/launch`, `/{id}/pause` | `GET`, `POST` | Multi-touch cold outreach campaign control. |
| `/api/v1/email` | `/drafts`, `/approve`, `/outbox` | `GET`, `POST` | Email drafting, approval gates, and delivery outbox. |
| `/api/v1/email` | `/suppression` | `GET`, `POST`, `DELETE`| Global bounce, complaint, and unsubscribe lists. |
| `/api/v1/integrations` | `/email-provider`, `/test` | `GET`, `POST` | Encrypted ESP credential storage (Resend/SendGrid/SES). |
| `/api/v1/schedules` | `/`, `/{id}` | `GET`, `POST` | Recurring automated crawl and lead update schedules. |
| `/api/v1/webhooks` | `/resend`, `/sendgrid`, `/ses` | `POST` | HMAC-SHA256 authenticated ESP event ingestion. |
| `/api/v1/audit` | `/` | `GET` | Multi-tenant append-only compliance audit logs. |
| `/api/v1/health` | `/`, `/ready`, `/live` | `GET` | Liveness, readiness, and subsystem probes. |

---

## 10. Testing & Verification

The platform features an automated test suite spanning unit tests, integration tests with database sessions, and end-to-end multi-agent acceptance tests.

### Running Test Suite

```bash
# Run complete test suite with coverage report
pytest apps/backend/tests -v --cov=app --cov-report=term-missing
```

### Test Hierarchy
1. **Unit Tests (`apps/backend/tests/unit/`):**
   - `test_ssrf_protection.py`: Verifies blocking of RFC 1918 IPs, IPv6 loopbacks, cloud metadata (`169.254.169.254`), and URL redirect bypasses.
   - `test_prompt_guard.py`: Validates quarantine delimiters and regex filtering of prompt injection triggers.
   - `test_html_parsers.py`: Asserts correct extraction of page titles, emails, social handles, and classified links.
   - `test_agent_contracts.py`: Enforces Pydantic V2 agent contract validation and JSON serialization.
   - `test_qualification_rules.py`: Validates deterministic lead qualification scoring logic and explanations.
   - `test_email_compliance.py`: Confirms CAN-SPAM physical postal address, unsubscribe headers, and suppression list enforcement.
   - `test_email_providers.py`: Tests provider adapters, dry-run safety modes, and failure recovery.
2. **Integration Tests (`apps/backend/tests/integration/`):**
   - `test_auth_api.py`: Validates registration, login, token refresh, and tenant isolation.
   - `test_companies_api.py`: Verifies company CRUD, search, pagination, and domain associations.
   - `test_email_outbox.py`: Asserts transactional outbox persistence, SHA-256 idempotency locks, and batch polling.
   - `test_webhooks.py`: Verifies HMAC-SHA256 signature verification and auto-suppression on bounce/complaint events.
3. **End-to-End Acceptance Tests (`apps/backend/tests/e2e/`):**
   - `test_full_workflow_acceptance.py`: Executes the complete pipeline from seed domain crawl to verified company facts, CRM lead qualification, email draft generation, human approval, outbox dispatch, and audit logging.

---

## 11. Operations & Observability

### Health Probes
- `GET /api/v1/health`: Overall system status.
- `GET /api/v1/health/ready`: Asserts database read/write readiness and Redis connectivity.
- `GET /api/v1/health/live`: Lightweight process liveness ping for Kubernetes/ECS.

### Structured Logging
All application logs are output in structured JSON format (`app/core/logging.py`) with standard OpenTelemetry-compatible fields:
```json
{
  "timestamp": "2026-10-17T21:30:00.123456Z",
  "level": "INFO",
  "logger": "app.orchestration.engine",
  "message": "Workflow transitioned to VERIFYING",
  "run_id": "r1000000-0000-0000-0000-000000000001",
  "workspace_id": "w0000000-0000-0000-0000-000000000001",
  "cost_usd": 0.042
}
```

---

## 12. Comprehensive Documentation Index

Deep-dive engineering artifacts are maintained in the [`docs/`](./docs/) directory:

- [Product Requirements Document (PRD)](./docs/PRD.md)
- [High-Level Design (HLD)](./docs/HLD.md)
- [Low-Level Design (LLD)](./docs/LLD.md)
- [Database Schema & Data Dictionary](./docs/DATABASE.md)
- [Multi-Agent Architecture & Contracts](./docs/AGENT_ARCHITECTURE.md)
- [Workflow State Machine & Sequence Diagrams](./docs/WORKFLOW_DIAGRAMS.md)
- [REST API Specification](./docs/API.md)
- [Security Architecture & Threat Model](./docs/SECURITY.md)
- [Email Compliance & Deliverability Guide](./docs/EMAIL_COMPLIANCE.md)
- [Production Deployment & Docker Guide](./docs/DEPLOYMENT.md)
- [Test Strategy & Verification Matrix](./docs/TESTING.md)
- [Operational Runbook & SRE Guide](./docs/OPERATIONS.md)
- [Environment Setup & Configuration](./docs/ENVIRONMENT_SETUP.md)
- [Troubleshooting & Diagnostics Guide](./docs/TROUBLESHOOTING.md)
- [Traceability Matrix](./docs/TRACEABILITY_MATRIX.md)

---

## License

This project is licensed under the MIT License — see the LICENSE file for details.
