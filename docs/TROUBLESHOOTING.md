# Troubleshooting Guide

### 1. Web Scraping & Crawling Issues

#### Problem: SSRF Filter blocks expected domains
- **Cause:** Domain resolves to an IP inside RFC 1918 subnets or loopback.
- **Resolution:** Verify domain DNS records via `nslookup <domain>`. Ensure you are not pointing to `localhost` or intranet hosts unless running under explicit mock test mode.

#### Problem: Target site blocks crawler with HTTP 403 or 429
- **Cause:** Cloudflare bot management, rate limit trigger, or missing user-agent.
- **Resolution:** Check `robots.txt`. Decrease concurrency via `SCRAPER_MAX_CONCURRENT_REQUESTS=1` and increase `SCRAPER_REQUEST_DELAY_SECONDS=2`.

#### Problem: JavaScript-heavy SPA content is empty
- **Cause:** Static HTTPX parser cannot execute client-side JavaScript.
- **Resolution:** Enable Playwright dynamic rendering adapter (`PLAYWRIGHT_ENABLED=true`). Ensure Playwright browsers are installed: `playwright install chromium`.

---

### 2. Multi-Agent & LLM Issues

#### Problem: LLM JSON Output Validation Error
- **Cause:** Model returned invalid markdown wrapper or missing required schema keys.
- **Resolution:** The platform's Pydantic contract layer uses robust JSON schema repair and sanitization. Check agent execution logs (`GET /api/v1/agents/executions`) to inspect raw LLM output.

#### Problem: Research Workflow Checkpoint Stuck in `RETRY_PENDING`
- **Cause:** Rate limits exceeded or model token quota exhausted.
- **Resolution:** Inspect `agent_executions` table for the specific error. Workflows can be manually resumed with `POST /api/v1/research/runs/{id}/resume`.

---

### 3. Outbound Email & Webhooks

#### Problem: Outbound emails are stuck in `PENDING_APPROVAL`
- **Cause:** `EMAIL_REQUIRE_APPROVAL=true` is enabled (production safety default).
- **Resolution:** Review and approve drafts in the CRM UI or via `POST /api/v1/email/approvals/{id}` with `decision: "APPROVED"`.

#### Problem: Webhook verification fails (`401 Unauthorized`)
- **Cause:** `EMAIL_WEBHOOK_SECRET` does not match provider signing secret.
- **Resolution:** Confirm provider webhook secret matches environment variable.
