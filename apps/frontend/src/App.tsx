import React, { useState, useEffect } from "react";
import { Sidebar } from "./components/Sidebar";
import { Header } from "./components/Header";
import { DashboardPage } from "./pages/DashboardPage";
import { CompaniesPage } from "./pages/CompaniesPage";
import { CompanyDetailPage } from "./pages/CompanyDetailPage";
import { ContactsPage } from "./pages/ContactsPage";
import { PipelinePage } from "./pages/PipelinePage";
import { ResearchConsolePage } from "./pages/ResearchConsolePage";
import { ApprovalQueuePage } from "./pages/ApprovalQueuePage";
import { CampaignsPage } from "./pages/CampaignsPage";
import { SuppressionPage } from "./pages/SuppressionPage";
import { AuditLogsPage } from "./pages/AuditLogsPage";
import { SettingsPage } from "./pages/SettingsPage";
import { api } from "./api/client";

export function App() {
  const [currentTab, setCurrentTab] = useState<string>("dashboard");
  const [selectedCompanyId, setSelectedCompanyId] = useState<string | null>(null);
  const [approvalCount, setApprovalCount] = useState<number>(0);

  useEffect(() => {
    checkApprovals();
  }, [currentTab]);

  const checkApprovals = async () => {
    try {
      const drafts = await api.getEmailDrafts("PENDING_APPROVAL");
      setApprovalCount(drafts ? drafts.length : 0);
    } catch {}
  };

  const handleSelectCompany = (id: string) => {
    setSelectedCompanyId(id);
    setCurrentTab("company_detail");
  };

  const getHeaderInfo = () => {
    switch (currentTab) {
      case "dashboard":
        return { title: "Executive Dashboard", subtitle: "Autonomous company intelligence & outreach overview" };
      case "companies":
        return { title: "Company Management", subtitle: "Enriched enterprise records, domains, and research profiles" };
      case "company_detail":
        return { title: "Company Intelligence Profile", subtitle: "In-depth extracted intelligence, citations, and scoring" };
      case "contacts":
        return { title: "Contact Directory", subtitle: "Discovered B2B contacts, titles, and permission status" };
      case "pipeline":
        return { title: "Commercial Pipeline", subtitle: "Kanban sales stages for qualified prospective accounts" };
      case "research":
        return { title: "Autonomous Research Agent", subtitle: "Launch multi-agent crawling, fact-checking, and profile extraction" };
      case "approvals":
        return { title: "Human Review Gate", subtitle: "Verify AI-drafted outreach before outbound email delivery" };
      case "campaigns":
        return { title: "Outreach Campaigns", subtitle: "Manage outreach series, rate limiting, and sending policies" };
      case "suppressions":
        return { title: "Email Suppression List", subtitle: "Global unsubscribes, bounces, and complaint protections" };
      case "audit":
        return { title: "Security & Audit Logs", subtitle: "Immutable event history and administrative actions" };
      case "settings":
        return { title: "Platform Settings", subtitle: "API credentials, deliverability sandbox, and integrations" };
      default:
        return { title: "Company Intelligence", subtitle: "Multi-agent sales automation" };
    }
  };

  const headerInfo = getHeaderInfo();

  return (
    <div className="flex min-h-screen bg-slate-950 text-slate-100">
      {/* Sidebar */}
      <Sidebar
        currentTab={currentTab === "company_detail" ? "companies" : currentTab}
        onSelectTab={(tab) => {
          setSelectedCompanyId(null);
          setCurrentTab(tab);
        }}
        approvalCount={approvalCount}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        <Header title={headerInfo.title} subtitle={headerInfo.subtitle} />

        <main className="flex-1 overflow-y-auto">
          {currentTab === "dashboard" && (
            <DashboardPage
              onNavigate={(tab) => {
                setSelectedCompanyId(null);
                setCurrentTab(tab);
              }}
              onSelectCompany={handleSelectCompany}
            />
          )}

          {currentTab === "companies" && (
            <CompaniesPage
              onSelectCompany={handleSelectCompany}
              onOpenResearch={() => setCurrentTab("research")}
            />
          )}

          {currentTab === "company_detail" && selectedCompanyId && (
            <CompanyDetailPage
              companyId={selectedCompanyId}
              onBack={() => {
                setSelectedCompanyId(null);
                setCurrentTab("companies");
              }}
            />
          )}

          {currentTab === "contacts" && <ContactsPage />}
          {currentTab === "pipeline" && <PipelinePage onSelectCompany={handleSelectCompany} />}
          {currentTab === "research" && <ResearchConsolePage onSelectCompany={handleSelectCompany} />}
          {currentTab === "approvals" && <ApprovalQueuePage />}
          {currentTab === "campaigns" && <CampaignsPage />}
          {currentTab === "suppressions" && <SuppressionPage />}
          {currentTab === "audit" && <AuditLogsPage />}
          {currentTab === "settings" && <SettingsPage />}
        </main>
      </div>
    </div>
  );
}

export default App;
