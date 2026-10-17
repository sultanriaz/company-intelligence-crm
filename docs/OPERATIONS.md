# Operations and Maintenance Runbook

### 1. Daily Health Checks & Monitoring
- API Health Check: `GET /api/v1/health` (HTTP 200 `{"status": "ok"}`)
- API Readiness Check: `GET /api/v1/ready` (checks DB, Redis, Celery)
- Queue Depth: Monitor Redis queue length for `research` and `email` tasks.
- Outbox Backlog: Query `SELECT COUNT(*) FROM email_messages WHERE status = 'PENDING'` (should stay close to 0).

### 2. Failure Recovery & Dead-Letter Handling
- **Interrupted Research Workflow:** Research jobs are checkpointed at every step. If a worker terminates, restart the job using `POST /api/v1/research/runs/{id}/resume`.
- **Email Delivery Failure:** Messages exceeding max retries (3) are marked `FAILED` with provider error details stored in `email_messages.status_details`.
- **Provider Outage:** Toggle active email provider via environment variable or workspace integration settings without service restart.

### 3. Backup and Disaster Recovery
- **PostgreSQL:** Daily WAL archiving and pg_dump:
  ```bash
  pg_dump -U postgres -d company_intelligence_crm -F c -b -v -f /backups/db_backup_$(date +%Y%m%d).dump
  ```
- **Redis:** Snapshot RDB persistence enabled with appendonly mode.
