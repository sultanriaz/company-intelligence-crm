# Low-Level Design (LLD)
## Subsystem Specifications and Internal Mechanics

### 1. Web Scraping & Crawling Subsystem (`app.scraping`)

#### 1.1 SSRF Protection (`app.security.ssrf`)
- **DNS Resolution:** Hostnames are resolved to canonical IP addresses before socket connection.
- **CIDR Blacklist:** 
  - `0.0.0.0/8`, `10.0.0.0/8`, `100.64.0.0/10`, `127.0.0.0/8`, `169.254.0.0/16`, `172.16.0.0/12`, `192.0.0.0/24`, `192.0.2.0/24`, `192.88.99.0/24`, `192.168.0.0/16`, `198.18.0.0/15`, `198.51.100.0/24`, `203.0.113.0/24`, `224.0.0.0/4`, `240.0.0.0/4`, `255.255.255.255/32`
  - IPv6: `::1`, `fc00::/7`, `fe80::/10`, `::ffff:0:0/96`
- **Scheme Validation:** Only `http` and `https` allowed. File, ftp, gopher, ldap, dict schemes rejected.
- **Redirect Validation:** Custom HTTPX transport hook validates every intermediate redirect target against the SSRF filter before following.

#### 1.2 Robots.txt Compliance (`app.scraping.robots`)
- Evaluates `robots.txt` per target domain with caching (TTL 1 hour).
- Checks user-agent rules and crawl-delay directives.
- If path is disallowed, crawling halts for that path with a documented skip reason.

#### 1.3 Rate Limiter & Concurrency (`app.scraping.rate_limiter`)
- Token bucket algorithm per host domain.
- Max concurrent requests per domain: configurable (default: 3).
- Respects HTTP 429 and `Retry-After` headers.

#### 1.4 HTML Parsing & Normalization (`app.scraping.parsers`)
- BeautifulSoup4 with `lxml`/`html.parser`.
- Text extraction removes scripts, styles, iframes, SVGs, and base64 binaries.
- Extracted sections:
  - Canonical URL, Page Title, Meta Description, OpenGraph metadata.
  - Page categorization: `About`, `Products/Services`, `Careers`, `Contact`, `Pricing`, `News/Blog`.
  - Structured contact discovery: public business emails, phones, social links (LinkedIn, Twitter/X, GitHub), physical address signals.
  - Content SHA256 hash for incremental change detection.

---

### 2. Multi-Agent Orchestration & Contracts (`app.agents`)

#### 2.1 Agent State Machine
States:
1. `CREATED`: Request initialized.
2. `VALIDATING`: Target domain validation and reachability check.
3. `DISCOVERING`: Link analysis and page categorization.
4. `EXTRACTING`: HTML retrieval and text extraction.
5. `RESEARCHING`: LLM semantic extraction of structured corporate profile.
6. `VERIFYING`: Fact cross-referencing and confidence scoring.
7. `ANALYZING`: Business insights and value propositions.
8. `SAVING`: CRM persistence of company, contacts, and facts.
9. `EMAIL_PREPARATION`: Draft generation.
10. `APPROVAL_PENDING`: Awaiting human review or auto-approval check.
11. `SENDING`: Transactional outbox staging and dispatch.
12. `COMPLETED`: Terminal successful state.

Terminal / Exception States:
- `FAILED`: Fatal unrecoverable error with structured error log.
- `CANCELLED`: User or timeout termination.
- `PARTIALLY_COMPLETED`: Partial extraction where non-critical steps failed.
- `RETRY_PENDING`: Scheduled for backoff retry.

#### 2.2 Pydantic Structured Contracts
Every agent consumes and produces strict schemas:
- `ResearchRequest`: Target URL, depth, allowed paths, priority, workspace_id.
- `DiscoveryResult`: List of discovered URLs, categories, crawl priorities.
- `ScrapedPage`: URL, title, normalized text, metadata, content_hash, status_code.
- `ResearchFact`: Field name, value, source URL, retrieved_at, confidence (0.0-1.0), status (`verified`, `provisional`, `conflicted`).
- `CompanyProfile`: Name, legal name, domain, industry, size, location, summary, products, technologies, contact channels, facts.
- `BusinessInsight`: Operational challenges (marked as hypotheses), opportunities, recommended outreach angle, value proposition.
- `LeadQualificationResult`: Dimension scores (industry, service, scale, opportunity, evidence) and transparent rationale.
- `EmailDraftResult`: Subject line, body text, referenced facts, recipient address, tone, compliance footer.

---

### 3. CRM & Data Integrity (`app.crm`, `app.models`)

#### 3.1 Domain & Company Deduplication
- Primary domain normalization: strip protocol, `www.`, path, lowercase.
- `company_domains` table ensures domain aliases map to a canonical `company_id`.
- Duplicate domain inserts resolve to the existing company record, updating enrichment history.

#### 3.2 Provenance Architecture
- Every item in `research_facts` stores `company_id`, `field_name`, `field_value`, `source_url`, `extracted_at`, `confidence_score`, and `verification_status`.
- Historical runs are archived in `research_runs` and `agent_executions`, allowing complete auditability of who/what gathered every claim.

---

### 4. Email Pipeline & Deliverability Architecture (`app.email`)

#### 4.1 Governance Checklist before Send
1. **Suppression Check:** Has recipient unsubscribed or previously bounced?
2. **Eligibility Check:** Does the contact have documented business relevance?
3. **Approval Status:** Is the draft approved (`email_approvals.status == 'APPROVED'`) or does campaign have explicit `auto_send_enabled=True`?
4. **Campaign Active:** Is the parent campaign active?
5. **Rate Limit:** Has the domain or workspace exceeded the hourly/daily cap?
6. **Double-Send Shield:** Idempotency key `campaign_id:contact_id:template_id` checked in `email_messages`.

#### 4.2 Pluggable Providers
Interface `BaseEmailProvider`:
- `send_email(to_email, subject, body_html, body_text, headers, idempotency_key) -> ProviderResult`
Implementations:
- `ResendEmailProvider`: REST API to `https://api.resend.com/emails`.
- `SendGridEmailProvider`: REST API to `https://api.sendgrid.com/v3/mail/send`.
- `SesEmailProvider`: Boto3 `sesv2.send_email`.
- `MockEmailProvider`: In-memory and database logged dispatch for dry-run/testing without network egress.
