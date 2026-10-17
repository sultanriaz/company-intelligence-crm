# REST API Specification (v1)

Base URL: `/api/v1`  
Authentication: Bearer JWT Token or `X-API-Key` header.

---

### Endpoint Catalog

#### 1. Authentication & Workspaces
- `POST /api/v1/auth/register` — Register workspace and initial admin user.
- `POST /api/v1/auth/login` — Authenticate and receive JWT access token.
- `GET /api/v1/auth/me` — Retrieve current authenticated user profile and permissions.
- `GET /api/v1/workspaces` — List accessible workspaces.

#### 2. Companies & Contacts (CRM)
- `GET /api/v1/companies` — Query company directory with domain, status, and industry filters.
- `POST /api/v1/companies` — Create company record manually or via seed domain.
- `GET /api/v1/companies/{id}` — Full company profile, associated contacts, facts, and activities.
- `PUT /api/v1/companies/{id}` — Update company details or pipeline stage.
- `GET /api/v1/contacts` — Contact directory with suppression and permission filters.
- `POST /api/v1/contacts` — Create or associate contact.
- `GET /api/v1/companies/{id}/activities` — Audit timeline of notes, calls, and email activities.

#### 3. Research & Multi-Agent Execution
- `POST /api/v1/research/runs` — Initiate research workflow for a target domain.
- `GET /api/v1/research/runs` — List recent and active research jobs.
- `GET /api/v1/research/runs/{id}` — Inspect execution status, agent progress, and checkpoints.
- `POST /api/v1/research/runs/{id}/cancel` — Cancel an in-flight research workflow.
- `GET /api/v1/agents/executions` — Audit logs of agent step executions and token usage.

#### 4. Lead Qualification & Pipelines
- `GET /api/v1/leads` — View qualified leads sorted by total score.
- `GET /api/v1/leads/{company_id}/score` — Detailed 5-factor score breakdown and explanations.
- `PUT /api/v1/leads/{company_id}/score` — Override or recompute qualification score.
- `GET /api/v1/pipelines` — CRM pipeline definitions and stages.

#### 5. Email Campaigns & Delivery
- `GET /api/v1/campaigns` — List outreach campaigns and status.
- `POST /api/v1/campaigns` — Create email campaign.
- `GET /api/v1/email/drafts` — Query pending email drafts.
- `POST /api/v1/email/approvals/{draft_id}` — Human approval/rejection decision.
- `POST /api/v1/email/messages/send-test` — Send test sandbox email.
- `GET /api/v1/email/suppressions` — View and manage email suppression list.
- `POST /api/v1/email/suppressions` — Manually add email to suppression list.

#### 6. Webhooks & Operational Health
- `POST /api/v1/webhooks/email/{provider}` — Ingest provider delivery/bounce webhooks (HMAC-SHA256 verified).
- `GET /api/v1/audit` — Tamper-evident audit log query.
- `GET /api/v1/health` — Liveness check.
- `GET /api/v1/ready` — Readiness check (Database, Redis, Worker connectivity).
