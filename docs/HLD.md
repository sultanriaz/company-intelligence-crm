# High-Level Design (HLD)
## Multi-Agent Company Intelligence & Outreach Automation Platform

### 1. System Architecture Overview

The platform uses a layered Clean Architecture pattern combining asynchronous event-driven background processing with a high-performance REST API and a responsive modern frontend.

```mermaid
flowchart TD
    subgraph Client Layer
        UI[React + TypeScript Dashboard]
        API_CLIENT[External Webhooks & API Consumers]
    end

    subgraph Ingress & Gateway Layer
        CORS[CORS & Security Headers]
        AUTH[JWT / API Key Authentication]
        RATE[Rate Limiter & SSRF Guard]
    end

    subgraph Application & API Layer
        FASTAPI[FastAPI REST API v1]
        REST_COMPANIES[Company & Contact Endpoints]
        REST_RESEARCH[Research & Execution Endpoints]
        REST_LEADS[Lead Scoring & Pipeline Endpoints]
        REST_EMAIL[Campaign & Outbox Endpoints]
        REST_WEBHOOKS[Provider Webhook Ingestion]
    end

    subgraph Workflow & Agent Orchestration
        SUPERVISOR[Supervisor State Machine Engine]
        CREW[Agent Task Coordinator]
        AGENT_DISC[Discovery Agent]
        AGENT_SCRP[Scraping Agent]
        AGENT_RES[Research Agent]
        AGENT_VERIF[Verification Agent]
        AGENT_INS[Insights Agent]
        AGENT_QUAL[Lead Qualification Agent]
        AGENT_CRM[CRM Sync Agent]
        AGENT_DRAFT[Email Drafting Agent]
        AGENT_DELIV[Delivery Agent]
    end

    subgraph Data & Storage Layer
        PG[(PostgreSQL 16 DB\n- Workspaces\n- Companies & Contacts\n- Facts & Provenance\n- Checkpoints & Outbox\n- Audit Logs)]
        REDIS[(Redis 7.4\n- Broker\n- Result Backend\n- Rate Limiting Tokens)]
        OUTBOX[Transactional Outbox Processor]
    end

    subgraph External Interfaces
        TARGET_WEB[Target Public Websites]
        LLM_GW[LLM Gateways: OpenAI / Anthropic / Local Mock]
        EMAIL_GW[Email Providers: Resend / SendGrid / SES / Dry-Run]
    end

    UI --> FASTAPI
    API_CLIENT --> FASTAPI
    FASTAPI --> REST_COMPANIES & REST_RESEARCH & REST_LEADS & REST_EMAIL & REST_WEBHOOKS
    REST_RESEARCH --> SUPERVISOR
    SUPERVISOR --> CREW
    CREW --> AGENT_DISC & AGENT_SCRP & AGENT_RES & AGENT_VERIF & AGENT_INS & AGENT_QUAL & AGENT_CRM & AGENT_DRAFT & AGENT_DELIV
    
    AGENT_SCRP --> TARGET_WEB
    AGENT_RES & AGENT_VERIF & AGENT_INS & AGENT_DRAFT --> LLM_GW
    AGENT_DELIV --> OUTBOX
    OUTBOX --> EMAIL_GW
    
    SUPERVISOR --> PG
    SUPERVISOR --> REDIS
    FASTAPI --> PG
```

---

### 2. Core Architectural Principles

1. **Deterministic Authority over Non-Deterministic Agents:**
   - LLMs generate structured proposals (JSON schemas via Pydantic).
   - Python core services strictly validate, enforce business rules, perform database operations, apply rate limits, check permissions, and manage outbox dispatches.
   - LLMs never directly write SQL, execute untrusted system commands, or initiate network dispatches without policy compliance.

2. **Durable Workflow State Machine:**
   Workflows progress through verifiable transitions:
   `CREATED` $\to$ `VALIDATING` $\to$ `DISCOVERING` $\to$ `EXTRACTING` $\to$ `RESEARCHING` $\to$ `VERIFYING` $\to$ `ANALYZING` $\to$ `SAVING` $\to$ `EMAIL_PREPARATION` $\to$ `APPROVAL_PENDING` $\to$ `SENDING` $\to$ `COMPLETED`
   (with terminal and recovery states: `FAILED`, `CANCELLED`, `PARTIALLY_COMPLETED`, `RETRY_PENDING`).
   Every transition saves an immutable snapshot in `workflow_checkpoints`.

3. **Multi-Tenancy & Workspace Isolation:**
   Every entity belongs to a `workspace_id`. Cross-workspace queries are strictly partitioned at the repository and ORM layer.

4. **Transactional Outbox for Outbound Communications:**
   Outbound emails are saved in an `outbox` table within the same ACID transaction as the state transition. A dedicated asynchronous outbox worker dispatches the email via the chosen provider adapter with an idempotency key, preventing phantom double-sends even under worker restarts or HTTP timeouts.

5. **Defense-in-Depth Web Extraction:**
   All crawled URLs pass through an SSRF validator blocking private subnets (RFC 1918, 127.0.0.0/8, 169.254.0.0/16, IPv6 loopback, cloud metadata endpoints). Redirect chains are strictly capped (max 5) and re-validated at each hop.
