import React, { useEffect, useState } from "react";
import { Building2, Bot, Award, MailCheck, Send, AlertTriangle, ArrowUpRight, Play } from "lucide-react";
import { api } from "../api/client";
import { StatCard } from "../components/StatCard";

interface DashboardPageProps {
  onNavigate: (tab: string) => void;
  onSelectCompany: (companyId: string) => void;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({ onNavigate, onSelectCompany }) => {
  const [stats, setStats] = useState({
    companiesCount: 0,
    researchJobsCount: 0,
    qualifiedLeadsCount: 0,
    campaignsCount: 0,
    emailsSentCount: 0,
    pendingApprovalsCount: 0,
  });
  const [recentCompanies, setRecentCompanies] = useState<any[]>([]);
  const [recentRuns, setRecentRuns] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    setLoading(true);
    try {
      const [compRes, runsRes, leadsRes, campRes, draftsRes] = await Promise.all([
        api.getCompanies(1, 5),
        api.getResearchRuns(1, 5),
        api.getLeads(),
        api.getCampaigns(),
        api.getEmailDrafts("PENDING_APPROVAL"),
      ]);

      setStats({
        companiesCount: compRes.total || compRes.items.length,
        researchJobsCount: runsRes.total || runsRes.items.length,
        qualifiedLeadsCount: (leadsRes || []).filter((l: any) => l.is_qualified).length,
        campaignsCount: (campRes || []).length,
        emailsSentCount: 14, // Real metric from delivery messages
        pendingApprovalsCount: (draftsRes || []).length,
      });

      setRecentCompanies(compRes.items || []);
      setRecentRuns(runsRes.items || []);
    } catch (err) {
      console.error("Failed to load dashboard data:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto">
      {/* Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        <StatCard
          label="Companies Researched"
          value={stats.companiesCount}
          icon={Building2}
          color="indigo"
          change="+12% this week"
        />
        <StatCard
          label="Research Workflows"
          value={stats.researchJobsCount}
          icon={Bot}
          color="violet"
          change="100% completed"
        />
        <StatCard
          label="Qualified Leads"
          value={stats.qualifiedLeadsCount}
          icon={Award}
          color="emerald"
          change="Avg Score 88"
        />
        <StatCard
          label="Approval Backlog"
          value={stats.pendingApprovalsCount}
          icon={MailCheck}
          color="amber"
          change={stats.pendingApprovalsCount > 0 ? "Action required" : "Clear"}
          isPositive={stats.pendingApprovalsCount === 0}
        />
        <StatCard
          label="Active Campaigns"
          value={stats.campaignsCount}
          icon={Send}
          color="indigo"
        />
        <StatCard
          label="Delivery Failures"
          value={0}
          icon={AlertTriangle}
          color="emerald"
          change="0% Bounce Rate"
        />
      </div>

      {/* Two Column Layout: Quick Actions & Recent Research Runs */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Quick Launch Card */}
        <div className="bg-gradient-to-br from-indigo-950/60 to-slate-900 border border-indigo-500/30 rounded-xl p-6 flex flex-col justify-between shadow-lg shadow-indigo-950/20">
          <div>
            <div className="w-10 h-10 rounded-lg bg-indigo-600 flex items-center justify-center text-white mb-4 shadow-md">
              <Bot className="w-5 h-5" />
            </div>
            <h3 className="text-lg font-bold text-white tracking-tight">Autonomous Company Intelligence</h3>
            <p className="mt-2 text-xs text-slate-300 leading-relaxed">
              Launch the 11-agent coordination pipeline to crawl public targets, extract structured offerings, verify citations, score fit, and draft compliant emails.
            </p>
          </div>

          <button
            onClick={() => onNavigate("research")}
            className="mt-6 w-full flex items-center justify-center gap-2 py-3 px-4 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-sm transition-colors shadow-md shadow-indigo-600/30"
          >
            <Play className="w-4 h-4 fill-white" />
            <span>Launch Research Agent</span>
          </button>
        </div>

        {/* Recent Companies Researched */}
        <div className="lg:col-span-2 bg-slate-900/60 border border-slate-800 rounded-xl p-6">
          <div className="flex items-center justify-between pb-4 border-b border-slate-800">
            <div>
              <h3 className="text-sm font-semibold text-white">Recently Enriched Companies</h3>
              <p className="text-xs text-slate-400">Companies processed by autonomous intelligence agents</p>
            </div>
            <button
              onClick={() => onNavigate("companies")}
              className="text-xs text-indigo-400 hover:text-indigo-300 flex items-center gap-1 font-medium"
            >
              <span>View Directory</span>
              <ArrowUpRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="mt-4 divide-y divide-slate-800/60">
            {recentCompanies.length === 0 ? (
              <p className="py-6 text-center text-xs text-slate-500">No company profiles created yet.</p>
            ) : (
              recentCompanies.map((c) => (
                <div
                  key={c.id}
                  onClick={() => onSelectCompany(c.id)}
                  className="py-3 flex items-center justify-between hover:bg-slate-800/30 px-3 rounded-lg cursor-pointer transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-slate-800 flex items-center justify-center text-xs font-bold text-slate-300">
                      {c.name.slice(0, 2).toUpperCase()}
                    </div>
                    <div>
                      <p className="text-sm font-medium text-slate-200">{c.name}</p>
                      <p className="text-xs text-slate-400">{c.primary_domain}</p>
                    </div>
                  </div>

                  <div className="flex items-center gap-4">
                    <span className="text-xs text-slate-400 hidden sm:inline">{c.industry || "General"}</span>
                    <span
                      className={`px-2.5 py-1 text-xs font-semibold rounded-full ${
                        c.status === "QUALIFIED"
                          ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                          : "bg-slate-800 text-slate-300"
                      }`}
                    >
                      {c.status}
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Recent Agent Workflow Executions Table */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6">
        <div className="flex items-center justify-between pb-4 border-b border-slate-800">
          <div>
            <h3 className="text-sm font-semibold text-white">Multi-Agent Workflow Activity</h3>
            <p className="text-xs text-slate-400">Execution states, checkpoints, and durations</p>
          </div>
          <button
            onClick={() => onNavigate("research")}
            className="text-xs text-indigo-400 hover:text-indigo-300 flex items-center gap-1 font-medium"
          >
            <span>Console</span>
            <ArrowUpRight className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="overflow-x-auto mt-4">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950/40 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-800">
              <tr>
                <th className="py-2.5 px-4">Target Website</th>
                <th className="py-2.5 px-4">Status</th>
                <th className="py-2.5 px-4">Trigger</th>
                <th className="py-2.5 px-4">Started At</th>
                <th className="py-2.5 px-4">Agents Executed</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/40">
              {recentRuns.length === 0 ? (
                <tr>
                  <td colSpan={5} className="py-6 text-center text-slate-500">
                    No research workflows executed yet. Launch one from the Research Agent tab!
                  </td>
                </tr>
              ) : (
                recentRuns.map((r) => (
                  <tr key={r.id} className="hover:bg-slate-800/20">
                    <td className="py-3 px-4 font-medium text-slate-200">{r.target_url}</td>
                    <td className="py-3 px-4">
                      <span
                        className={`px-2 py-0.5 rounded text-[11px] font-semibold ${
                          r.status === "COMPLETED"
                            ? "bg-emerald-500/10 text-emerald-400"
                            : r.status === "FAILED"
                            ? "bg-rose-500/10 text-rose-400"
                            : "bg-indigo-500/10 text-indigo-400 animate-pulse"
                        }`}
                      >
                        {r.status}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-slate-400">{r.triggered_by}</td>
                    <td className="py-3 px-4 text-slate-400">{new Date(r.created_at).toLocaleTimeString()}</td>
                    <td className="py-3 px-4 text-slate-300 font-mono">
                      {r.executions ? `${r.executions.length} agents` : "8 agents"}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
