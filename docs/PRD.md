# Product Requirements Document (PRD)
## AI-Powered Multi-Agent Company Intelligence & Outreach Automation Platform

**Document Version:** 1.0.0  
**Status:** Approved  
**Classification:** Production Engineering Specification  

---

### 1. Executive Summary & Vision
The AI-Powered Multi-Agent Company Intelligence & Outreach Automation Platform is an enterprise-grade system engineered to autonomously discover, crawl, research, verify, qualify, and engage prospective B2B organizations. 

Unlike conventional sales intelligence tools that depend on opaque SaaS silos or naive web scrapers, this platform:
- Implements an autonomous multi-agent hierarchy orchestrated through explicit state-machine checkpoints and strongly typed Pydantic contracts.
- Strictly separates non-deterministic AI generation from deterministic policy enforcement (SSRF protection, robots.txt, robots exclusion, legal basis checks, suppression lists, approval gates, transactional outbox).
- Provides a self-contained, audit-compliant custom CRM and data lake with immutable provenance for every fact and claim.
- Features multi-provider email dispatching (Resend, SendGrid, Amazon SES, and dry-run adapters) with strict double-send prevention and cryptographically verified webhook ingestion.

---

### 2. Functional Requirements (FR)

| ID | Module | Description | Criticality |
|---|---|---|---|
| **FR-01** | Discovery | Autonomous crawling of authorized target domains up to configurable depth with internal link discovery, duplicate URL detection, and page categorization (About, Services, Careers, Contact, News). | P0 |
| **FR-02** | Scraping Engine | High-throughput HTTPX client with rate limiting, per-domain concurrency, robots.txt compliance, and fallback to Playwright dynamic rendering for SPA/JavaScript-heavy sites. | P0 |
| **FR-03** | Security Sandbox | Strict SSRF defense blocking loopback, RFC1918 private subnets, cloud metadata IPs (169.254.169.254), and dangerous redirect chains. | P0 |
| **FR-04** | Research Agent | Extraction of structured corporate data (industry, products, tech stack, leadership, geographic footprint) with strict attribution to exact source URLs and timestamps. | P0 |
| **FR-05** | Fact Verification | Cross-referencing findings across multiple pages/sources, assigning evidence quality confidence scores (0.00-1.00), and flagging unverified claims or hallucinations. | P0 |
| **FR-06** | Business Insights | Extraction of verified business summaries, operational challenges (flagged explicitly as testable hypotheses), and company-specific value propositions. | P1 |
| **FR-07** | Lead Qualification | Configurable multi-dimensional weighted scoring (0-100) combining industry fit, service compatibility, company scale, opportunity indicators, and evidence quality with transparent breakdown explanations. | P0 |
| **FR-08** | Custom CRM API | Full RESTful CRM storing Workspaces, Companies, Contacts, Research Runs, Facts, Pipelines, Stages, Activities, and Timeline events with PostgreSQL transactional integrity. | P0 |
| **FR-09** | Email Drafting | AI-assisted generation of context-aware, evidence-based business outreach drafts referencing only verified facts; strictly rejecting deceptive or fabricated familiarity. | P1 |
| **FR-10** | Compliance & Approvals | Multi-layer outbound governance: mandatory human approval queue by default, campaign activation checks, lawful basis validation (GDPR/CAN-SPAM), and global suppression lists. | P0 |
| **FR-11** | Email Delivery | Pluggable delivery adapters (Resend, SendGrid, AWS SES, Dry-Run Mock) utilizing a Transactional Outbox pattern to prevent duplicate dispatch under network partition or timeouts. | P0 |
| **FR-12** | Tracking & Webhooks | Cryptographically authenticated webhook processing for delivery, bounce, complaint, open, click, and unsubscribe events; automatic suppression upon bounce or complaint. | P0 |
| **FR-13** | Scheduling & Recrawl | Celery Beat & internal scheduler supporting cron/interval automated re-crawling, incremental enrichment, and scheduled follow-up triggers. | P1 |
| **FR-14** | CRM Frontend | Modern responsive React/TypeScript Single Page Application featuring interactive Dashboard, Company Directory, Pipeline Kanban, Research Console, and Approval Inbox. | P0 |
| **FR-15** | Audit & RBAC | Multi-tenant workspace isolation with Role-Based Access Control (Admin, Member, Viewer) and tamper-evident structured audit logging. | P0 |

---

### 3. Non-Functional Requirements (NFR)

- **Reliability & Fault Tolerance (NFR-01):** Agent supervisor must persist state at every transition (`workflow_checkpoints`). Interrupted workflows must resume without data corruption.
- **Performance & Scalability (NFR-02):** Scraping engine must support asynchronous non-blocking I/O with per-domain token bucket rate limiting (default 3 concurrent requests, configurable delay).
- **Security & Privacy (NFR-03):** Zero prompt-injection bypass of business logic. Scraped HTML must be sanitized before processing. Zero storage of plaintext API keys or credentials; AES-GCM-256 encryption for integration secrets.
- **Observability (NFR-04):** OpenTelemetry-compatible structured JSON logging with correlation IDs, trace IDs, and step-level execution timers across all agents.
- **Testability & Determinism (NFR-05):** At least 85% test coverage for critical application paths. Complete offline testability via deterministic mock adapters and static HTML fixtures without live external API dependencies.

---

### 4. User Personas
1. **Sales Development Representative (SDR):** Submits company targets, reviews generated company intelligence and qualification scores, edits and approves AI-generated email drafts.
2. **Growth / Marketing Lead:** Configures scoring weights, sets outreach campaign parameters, monitors deliverability and bounce rates, manages suppression lists.
3. **System Administrator / Compliance Officer:** Manages workspace members, inspects audit trails, reviews outbound email compliance status, and configures provider credentials.
