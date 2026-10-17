"""initial schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-10-17 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Workspaces
    op.create_table(
        'workspaces',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False, unique=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 2. Users
    op.create_table(
        'users',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('workspace_id', sa.String(length=36), sa.ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False, server_default='MEMBER'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 3. Pipelines & Stages
    op.create_table(
        'crm_pipelines',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('workspace_id', sa.String(length=36), sa.ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        'crm_stages',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('pipeline_id', sa.String(length=36), sa.ForeignKey('crm_pipelines.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('order_index', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('color', sa.String(length=20), nullable=False, server_default='#6366f1'),
    )

    # 4. Companies
    op.create_table(
        'companies',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('workspace_id', sa.String(length=36), sa.ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('primary_domain', sa.String(length=255), nullable=False),
        sa.Column('legal_name', sa.String(length=255), nullable=True),
        sa.Column('industry', sa.String(length=100), nullable=True),
        sa.Column('employee_range', sa.String(length=100), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('headquarters', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='PROSPECT'),
        sa.Column('pipeline_stage_id', sa.String(length=36), sa.ForeignKey('crm_stages.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('workspace_id', 'primary_domain', name='uq_workspace_company_domain'),
    )

    # 5. Company Domains
    op.create_table(
        'company_domains',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('company_id', sa.String(length=36), sa.ForeignKey('companies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('domain', sa.String(length=255), nullable=False),
        sa.Column('is_primary', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('company_id', 'domain', name='uq_company_domain'),
    )

    # 6. Contacts
    op.create_table(
        'contacts',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('workspace_id', sa.String(length=36), sa.ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=False),
        sa.Column('company_id', sa.String(length=36), sa.ForeignKey('companies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('first_name', sa.String(length=100), nullable=False),
        sa.Column('last_name', sa.String(length=100), nullable=False, server_default=''),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('title', sa.String(length=150), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('linkedin_url', sa.String(length=500), nullable=True),
        sa.Column('provenance_url', sa.String(length=1000), nullable=True),
        sa.Column('permission_status', sa.String(length=50), nullable=False, server_default='LEGITIMATE_INTEREST'),
        sa.Column('is_suppressed', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('workspace_id', 'email', name='uq_workspace_contact_email'),
    )

    # 7. Research Runs
    op.create_table(
        'research_runs',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('workspace_id', sa.String(length=36), sa.ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=False),
        sa.Column('company_id', sa.String(length=36), sa.ForeignKey('companies.id', ondelete='SET NULL'), nullable=True),
        sa.Column('target_url', sa.String(length=1000), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='CREATED'),
        sa.Column('triggered_by', sa.String(length=100), nullable=False, server_default='MANUAL'),
        sa.Column('config_snapshot', sa.Text(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    )

    # 8. Agent Executions
    op.create_table(
        'agent_executions',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('research_run_id', sa.String(length=36), sa.ForeignKey('research_runs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('agent_name', sa.String(length=100), nullable=False),
        sa.Column('state', sa.String(length=50), nullable=False),
        sa.Column('input_payload', sa.Text(), nullable=True),
        sa.Column('output_payload', sa.Text(), nullable=True),
        sa.Column('tokens_used', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('cost_usd', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('duration_ms', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 9. Workflow Checkpoints
    op.create_table(
        'workflow_checkpoints',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('research_run_id', sa.String(length=36), sa.ForeignKey('research_runs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('state', sa.String(length=50), nullable=False),
        sa.Column('step_index', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('state_data', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 10. Company Sources, Facts & Reports
    op.create_table(
        'company_sources',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('company_id', sa.String(length=36), sa.ForeignKey('companies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('run_id', sa.String(length=36), sa.ForeignKey('research_runs.id', ondelete='SET NULL'), nullable=True),
        sa.Column('url', sa.String(length=1000), nullable=False),
        sa.Column('http_status', sa.Integer(), nullable=False, server_default='200'),
        sa.Column('content_hash', sa.String(length=64), nullable=False),
        sa.Column('raw_text', sa.Text(), nullable=True),
        sa.Column('retrieved_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        'research_facts',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('company_id', sa.String(length=36), sa.ForeignKey('companies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('run_id', sa.String(length=36), sa.ForeignKey('research_runs.id', ondelete='SET NULL'), nullable=True),
        sa.Column('field_name', sa.String(length=100), nullable=False),
        sa.Column('field_value', sa.Text(), nullable=False),
        sa.Column('source_url', sa.String(length=1000), nullable=False),
        sa.Column('confidence_score', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('verification_status', sa.String(length=50), nullable=False, server_default='VERIFIED'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        'research_reports',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('company_id', sa.String(length=36), sa.ForeignKey('companies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('run_id', sa.String(length=36), sa.ForeignKey('research_runs.id', ondelete='SET NULL'), nullable=True),
        sa.Column('executive_summary', sa.Text(), nullable=False),
        sa.Column('challenges_hypotheses', sa.Text(), nullable=True),
        sa.Column('opportunities', sa.Text(), nullable=True),
        sa.Column('tech_stack', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 11. Lead Scores & Explanations
    op.create_table(
        'lead_scores',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('company_id', sa.String(length=36), sa.ForeignKey('companies.id', ondelete='CASCADE'), unique=True, nullable=False),
        sa.Column('total_score', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('industry_score', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('service_score', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('scale_score', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('opportunity_score', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('evidence_score', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_qualified', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('qualification_notes', sa.Text(), nullable=True),
        sa.Column('scored_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        'lead_score_explanations',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('lead_score_id', sa.String(length=36), sa.ForeignKey('lead_scores.id', ondelete='CASCADE'), nullable=False),
        sa.Column('dimension', sa.String(length=50), nullable=False),
        sa.Column('score_assigned', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('max_score', sa.Integer(), nullable=False, server_default='25'),
        sa.Column('reason', sa.Text(), nullable=False),
    )

    # 12. CRM Activities
    op.create_table(
        'crm_activities',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('workspace_id', sa.String(length=36), sa.ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=False),
        sa.Column('company_id', sa.String(length=36), sa.ForeignKey('companies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('contact_id', sa.String(length=36), sa.ForeignKey('contacts.id', ondelete='SET NULL'), nullable=True),
        sa.Column('activity_type', sa.String(length=50), nullable=False),
        sa.Column('details', sa.Text(), nullable=False),
        sa.Column('created_by', sa.String(length=100), nullable=False, server_default='SYSTEM'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 13. Email Campaigns, Templates & Drafts
    op.create_table(
        'email_templates',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('workspace_id', sa.String(length=36), sa.ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('subject_template', sa.String(length=500), nullable=False),
        sa.Column('body_template', sa.Text(), nullable=False),
        sa.Column('variables', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        'email_campaigns',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('workspace_id', sa.String(length=36), sa.ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=False),
        sa.Column('template_id', sa.String(length=36), sa.ForeignKey('email_templates.id', ondelete='SET NULL'), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='DRAFT'),
        sa.Column('auto_send_enabled', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('daily_limit', sa.Integer(), nullable=False, server_default='50'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        'campaign_recipients',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('campaign_id', sa.String(length=36), sa.ForeignKey('email_campaigns.id', ondelete='CASCADE'), nullable=False),
        sa.Column('contact_id', sa.String(length=36), sa.ForeignKey('contacts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='QUEUED'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('campaign_id', 'contact_id', name='uq_campaign_recipient'),
    )
    op.create_table(
        'email_drafts',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('campaign_id', sa.String(length=36), sa.ForeignKey('email_campaigns.id', ondelete='CASCADE'), nullable=True),
        sa.Column('contact_id', sa.String(length=36), sa.ForeignKey('contacts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('subject', sa.String(length=500), nullable=False),
        sa.Column('body_html', sa.Text(), nullable=False),
        sa.Column('body_text', sa.Text(), nullable=False),
        sa.Column('referenced_facts', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='PENDING_APPROVAL'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        'email_approvals',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('draft_id', sa.String(length=36), sa.ForeignKey('email_drafts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('reviewed_by', sa.String(length=100), nullable=False),
        sa.Column('decision', sa.String(length=50), nullable=False),
        sa.Column('feedback', sa.Text(), nullable=True),
        sa.Column('decided_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        'email_messages',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('workspace_id', sa.String(length=36), sa.ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=False),
        sa.Column('draft_id', sa.String(length=36), sa.ForeignKey('email_drafts.id', ondelete='SET NULL'), nullable=True),
        sa.Column('contact_id', sa.String(length=36), sa.ForeignKey('contacts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('provider_name', sa.String(length=50), nullable=False, server_default='mock'),
        sa.Column('provider_message_id', sa.String(length=255), nullable=True),
        sa.Column('idempotency_key', sa.String(length=255), unique=True, nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='PENDING'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        'email_events',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('email_message_id', sa.String(length=36), sa.ForeignKey('email_messages.id', ondelete='CASCADE'), nullable=False),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('payload', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        'email_suppressions',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('workspace_id', sa.String(length=36), sa.ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('reason', sa.String(length=50), nullable=False, server_default='UNSUBSCRIBE'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('workspace_id', 'email', name='uq_workspace_email_suppression'),
    )

    # 14. Audit, Integrations, Schedules, Webhooks
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('workspace_id', sa.String(length=36), sa.ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('resource_type', sa.String(length=100), nullable=False),
        sa.Column('resource_id', sa.String(length=36), nullable=True),
        sa.Column('ip_address', sa.String(length=50), nullable=True),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        'integration_configs',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('workspace_id', sa.String(length=36), sa.ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=False),
        sa.Column('provider_type', sa.String(length=50), nullable=False),
        sa.Column('encrypted_credentials', sa.Text(), nullable=False),
        sa.Column('is_enabled', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('workspace_id', 'provider_type', name='uq_workspace_provider'),
    )
    op.create_table(
        'scheduled_tasks',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('workspace_id', sa.String(length=36), sa.ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=False),
        sa.Column('task_type', sa.String(length=100), nullable=False),
        sa.Column('schedule_cron', sa.String(length=100), nullable=False),
        sa.Column('last_run_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('next_run_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('payload', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        'webhook_events',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('provider', sa.String(length=50), nullable=False),
        sa.Column('event_id', sa.String(length=255), nullable=False, unique=True),
        sa.Column('payload', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='PROCESSED'),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    pass
