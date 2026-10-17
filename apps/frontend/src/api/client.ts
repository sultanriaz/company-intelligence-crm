const API_BASE = "/api/v1";

class ApiClient {
  private token: string | null = null;

  setToken(token: string) {
    this.token = token;
    localStorage.setItem("auth_token", token);
  }

  getToken(): string | null {
    if (!this.token) {
      this.token = localStorage.getItem("auth_token");
    }
    return this.token;
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${API_BASE}${endpoint}`;
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...(options.headers as Record<string, string>),
    };

    const token = this.getToken();
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    const response = await fetch(url, { ...options, headers });
    if (!response.ok) {
      let errorMsg = `HTTP Error ${response.status}: ${response.statusText}`;
      try {
        const errJson = await response.json();
        if (errJson.detail) errorMsg = errJson.detail;
        else if (errJson.message) errorMsg = errJson.message;
      } catch {}
      throw new Error(errorMsg);
    }
    return response.json();
  }

  // Auth
  async login(email: string, password: string) {
    const res = await this.request<{ access_token: string; workspace_id: string; role: string }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    this.setToken(res.access_token);
    return res;
  }

  async getMe() {
    return this.request<any>("/auth/me");
  }

  // Companies
  async getCompanies(page = 1, pageSize = 20, status?: string, search?: string) {
    let url = `/companies?page=${page}&page_size=${pageSize}`;
    if (status) url += `&status=${encodeURIComponent(status)}`;
    if (search) url += `&search=${encodeURIComponent(search)}`;
    return this.request<{ items: any[]; total: number; page: number; total_pages: number }>(url);
  }

  async getCompany(id: string) {
    return this.request<any>(`/companies/${id}`);
  }

  async createCompany(targetUrl: string, name?: string) {
    return this.request<any>("/companies", {
      method: "POST",
      body: JSON.stringify({ target_url: targetUrl, name }),
    });
  }

  async getCompanyActivities(id: string) {
    return this.request<any[]>(`/companies/${id}/activities`);
  }

  // Contacts
  async getContacts(page = 1, pageSize = 20, companyId?: string) {
    let url = `/contacts?page=${page}&page_size=${pageSize}`;
    if (companyId) url += `&company_id=${companyId}`;
    return this.request<{ items: any[]; total: number; page: number }>(url);
  }

  // Research Runs
  async getResearchRuns(page = 1, pageSize = 20) {
    return this.request<{ items: any[]; total: number }>(`/research/runs?page=${page}&page_size=${pageSize}`);
  }

  async getResearchRun(runId: string) {
    return this.request<any>(`/research/runs/${runId}`);
  }

  async startResearchRun(targetUrl: string, depth = 2, maxPages = 15, includeEmail = true) {
    return this.request<any>("/research/runs", {
      method: "POST",
      body: JSON.stringify({
        target_url: targetUrl,
        crawl_depth: depth,
        max_pages: maxPages,
        include_email_generation: includeEmail,
      }),
    });
  }

  // Pipelines & Leads
  async getPipelines() {
    return this.request<any[]>("/pipelines");
  }

  async getLeads() {
    return this.request<any[]>("/leads");
  }

  async getLeadScore(companyId: string) {
    return this.request<any>(`/leads/${companyId}/score`);
  }

  // Campaigns & Email
  async getCampaigns() {
    return this.request<any[]>("/campaigns");
  }

  async getEmailDrafts(status?: string) {
    let url = "/email/drafts";
    if (status) url += `?status=${encodeURIComponent(status)}`;
    return this.request<any[]>(url);
  }

  async decideApproval(draftId: string, decision: "APPROVED" | "REJECTED", feedback?: string) {
    return this.request<any>(`/email/approvals/${draftId}`, {
      method: "POST",
      body: JSON.stringify({ decision, feedback }),
    });
  }

  async sendTestEmail(toEmail: string) {
    return this.request<any>("/email/messages/send-test", {
      method: "POST",
      body: JSON.stringify({ to_email: toEmail }),
    });
  }

  // Suppressions
  async getSuppressions() {
    return this.request<any[]>("/email/suppressions");
  }

  async addSuppression(email: string, reason = "MANUAL") {
    return this.request<any>("/email/suppressions", {
      method: "POST",
      body: JSON.stringify({ email, reason }),
    });
  }

  // Audit Logs
  async getAuditLogs() {
    return this.request<any[]>("/audit");
  }
}

export const api = new ApiClient();
