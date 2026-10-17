# Testing Strategy & Quality Assurance

### 1. Test Architecture

The test suite enforces at least 85% line coverage on business-critical Python code. It is designed to execute completely offline without live external credentials using mocks and local fixtures, with an optional live integration suite.

```text
apps/backend/tests/
  |-- unit/
  |   |-- test_ssrf_protection.py
  |   |-- test_robots_parser.py
  |   |-- test_html_parsers.py
  |   |-- test_agent_contracts.py
  |   |-- test_prompt_guard.py
  |   |-- test_qualification_rules.py
  |   |-- test_email_compliance.py
  |-- integration/
  |   |-- test_auth_api.py
  |   |-- test_companies_api.py
  |   |-- test_research_api.py
  |   |-- test_email_outbox.py
  |   |-- test_webhooks.py
  |   |-- test_duplicate_send_prevention.py
  |-- e2e/
  |   |-- test_full_workflow_acceptance.py
  |-- fixtures/
      |-- sample_site.html
      |-- sample_spa_page.html
```

### 2. Running Automated Tests

```bash
# Run complete test suite with coverage
pytest --cov=app --cov-report=term-missing --cov-fail-under=85

# Run specifically unit tests
pytest tests/unit

# Run end-to-end integration scenario
pytest tests/e2e/test_full_workflow_acceptance.py
```
