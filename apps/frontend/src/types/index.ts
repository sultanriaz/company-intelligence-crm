export interface Company {
  id: string;
  workspace_id: string;
  name: string;
  primary_domain: string;
  legal_name?: string;
  industry?: string;
  employee_range?: string;
  description?: string;
  headquarters?: string;
  status: string;
  pipeline_stage_id?: string;
  created_at: string;
  updated_at: string;
  total_score?: number;
  is_qualified?: boolean;
}

export interface ResearchFact {
  id: string;
  field_name: string;
  field_value: string;
  source_url: string;
  confidence_score: number;
  verification_status: string;
  created_at: string;
}

export interface ResearchReport {
  id: string;
  executive_summary: string;
  challenges_hypotheses?: string;
  opportunities?: string;
  tech_stack?: string;
  created_at: string;
}

export interface CompanyDetail extends Company {
  facts: ResearchFact[];
  reports: ResearchReport[];
}

export interface Contact {
  id: string;
  workspace_id: string;
  company_id: string;
  first_name: string;
  last_name: string;
  email: string;
  title?: string;
  phone?: string;
  linkedin_url?: string;
  provenance_url?: string;
  permission_status: string;
  is_suppressed: boolean;
  created_at: string;
}

export interface AgentExecution {
  id: string;
  agent_name: string;
  state: string;
  tokens_used: number;
  cost_usd: number;
  duration_ms: number;
  error_message?: string;
  created_at: string;
}

export interface ResearchRun {
  id: string;
  workspace_id: string;
  company_id?: string;
  target_url: string;
  status: string;
  triggered_by: string;
  error_message?: string;
  created_at: string;
  completed_at?: string;
  executions: AgentExecution[];
  checkpoints: any[];
}

export interface ScoreExplanation {
  dimension: string;
  score_assigned: number;
  max_score: number;
  reason: string;
}

export interface LeadScore {
  id: string;
  company_id: string;
  total_score: number;
  industry_score: number;
  service_score: number;
  scale_score: number;
  opportunity_score: number;
  evidence_score: number;
  is_qualified: boolean;
  qualification_notes?: string;
  scored_at: string;
  explanations: ScoreExplanation[];
}

export interface PipelineStage {
  id: string;
  name: string;
  order_index: number;
  color: string;
}

export interface CRMPipeline {
  id: string;
  workspace_id: string;
  name: string;
  is_default: boolean;
  stages: PipelineStage[];
}

export interface Campaign {
  id: string;
  workspace_id: string;
  name: string;
  status: string;
  auto_send_enabled: boolean;
  daily_limit: number;
  created_at: string;
}

export interface EmailDraft {
  id: string;
  campaign_id?: string;
  contact_id: string;
  subject: string;
  body_html: string;
  body_text: string;
  status: string;
  referenced_facts?: string;
  created_at: string;
  contact?: Contact;
}

export interface EmailSuppression {
  id: string;
  workspace_id: string;
  email: string;
  reason: string;
  created_at: string;
}

export interface AuditLog {
  id: string;
  workspace_id: string;
  action: string;
  resource_type: string;
  details?: string;
  ip_address?: string;
  timestamp: string;
}
