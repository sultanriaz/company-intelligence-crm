# Outbound Email Compliance & Deliverability Policy

### 1. Regulatory Governance (GDPR, CAN-SPAM, CASL)

1. **Lawful Basis & Legitimate Interest:**
   - Emails must never be sent solely because an email was scraped.
   - The platform verifies B2B business relevance (industry alignment, company scale, demonstrable service fit).
   - Records store `provenance_url` and `permission_status` (`LEGITIMATE_INTEREST` or `EXPLICIT_CONSENT`).

2. **Mandatory Human-in-the-Loop Approval:**
   - By default, all campaigns require human review of generated drafts (`EMAIL_REQUIRE_APPROVAL=true`).
   - Automated sending (`EMAIL_AUTO_SEND_ENABLED=true`) can only be turned on by Workspace Admins after recipient eligibility filters pass.

3. **Opt-Out & Unsubscribe Enforcement:**
   - Every outbound email template must include a physical postal address and a clear, functional one-click unsubscribe mechanism.
   - Upon receiving an unsubscribe or complaint signal:
     - The email is immediately written to `email_suppressions` (indexed per workspace).
     - Any queued or future drafts targeting that email address are aborted.

4. **Sender Identity & Technical Deliverability:**
   - Senders must use verified custom domains.
   - SPF (`v=spf1 include:... ~all`), DKIM (2048-bit key), and DMARC (`v=DMARC1; p=reject; rua=mailto:...`) records must be configured on sending domains.
   - The platform enforces `EMAIL_FROM_ADDRESS`, `EMAIL_FROM_NAME`, and `EMAIL_REPLY_TO` consistency.

5. **Dry-Run & Sandbox Safeguards:**
   - When `EMAIL_DRY_RUN=true`, outbound messages are safely routed to the mock adapter, recorded in the database, and reflected in the UI without external network egress.
