# Requirements Traceability Matrix (RTM)

This matrix maps every functional requirement (FR), non-functional requirement (NFR), and acceptance criteria to the implementing modules and automated tests.

| Req ID | Requirement | Primary Implementation Files | Test Suite / Verification |
|---|---|---|---|
| **FR-01** | Website Discovery & Crawling | `app/scraping/crawler.py`<br>`app/agents/discovery.py` | `tests/unit/test_discovery.py`<br>`tests/unit/test_crawler.py` |
| **FR-02** | HTML Scraping & Content Parsing | `app/scraping/parsers.py`<br>`app/scraping/playwright_client.py` | `tests/unit/test_html_parsers.py` |
| **FR-03** | SSRF Defense & URL Validation | `app/security/ssrf.py`<br>`app/scraping/client.py` | `tests/unit/test_ssrf_protection.py` |
| **FR-04** | Company Research & Extraction | `app/agents/research.py`<br>`app/research/profile_builder.py` | `tests/unit/test_research_agent.py` |
| **FR-05** | Fact Verification & Citations | `app/agents/verification.py`<br>`app/verification/fact_checker.py` | `tests/unit/test_fact_verification.py` |
| **FR-06** | Business Insights & Value Props | `app/agents/insights.py`<br>`app/insights/analysis_engine.py` | `tests/unit/test_insights_agent.py` |
| **FR-07** | Lead Qualification & Weighted Scoring | `app/agents/qualification.py`<br>`app/qualification/scorer.py` | `tests/unit/test_qualification_rules.py` |
| **FR-08** | Custom CRM API & Data Lake | `app/crm/service.py`<br>`app/api/v1/companies.py`<br>`app/api/v1/contacts.py` | `tests/integration/test_companies_api.py` |
| **FR-09** | Personalized Email Generation | `app/agents/email_draft.py`<br>`app/email/template_engine.py` | `tests/unit/test_email_draft.py` |
| **FR-10** | Compliance, Approvals & Suppression | `app/email/compliance.py`<br>`app/api/v1/email.py` | `tests/unit/test_email_compliance.py` |
| **FR-11** | Email Outbox & Delivery Adapters | `app/email/outbox.py`<br>`app/email/providers/` | `tests/integration/test_email_outbox.py` |
| **FR-12** | Tracking Webhooks & Auto-Suppression | `app/api/v1/webhooks.py`<br>`app/email/tracking.py` | `tests/integration/test_webhooks.py` |
| **FR-13** | Scheduling & Incremental Recrawl | `app/workers/scheduler.py`<br>`app/api/v1/schedules.py` | `tests/unit/test_scheduler.py` |
| **FR-14** | Custom CRM Single Page App | `apps/frontend/src/` | Frontend build & smoke verification |
| **FR-15** | RBAC, Audit Logging & Workspaces | `app/auth/permissions.py`<br>`app/api/v1/audit.py` | `tests/integration/test_auth_api.py` |
| **E2E** | End-to-End Acceptance Scenario | `app/orchestration/engine.py`<br>`app/agents/supervisor.py` | `tests/e2e/test_full_workflow_acceptance.py` |
