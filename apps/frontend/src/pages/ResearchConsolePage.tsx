import React, { useState } from "react";
import { Bot, Play, CheckCircle2, AlertCircle, Loader2, ExternalLink, ShieldCheck, Zap } from "lucide-react";
import { api } from "../api/client";

interface ResearchConsoleProps {
  onSelectCompany: (id: string) => void;
}

export const ResearchConsolePage: React.FC<ResearchConsoleProps> = ({ onSelectCompany }) => {
  const [targetUrl, setTargetUrl] = useState("https://acme.example.com");
  const [crawlDepth, setCrawlDepth] = useState(2);
  const [maxPages, setMaxPages] = useState(15);
  const [includeEmail, setIncludeEmail] = useState(true);

  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<any | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeStepId, setActiveStepId] = useState<string>("VALIDATING");
  const [completedStepIds, setCompletedStepIds] = useState<string[]>([]);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);

  const workflowSteps = [
    { id: "VALIDATING", label: "Target Validation & SSRF Check" },
    { id: "DISCOVERING", label: "Discovery Agent (URL Exploration)" },
    { id: "EXTRACTING", label: "Scraping Agent (HTML & Metadata)" },
    { id: "RESEARCHING", label: "Research Agent (Profile & Offerings)" },
    { id: "VERIFYING", label: "Verification Agent (Fact Provenance)" },
    { id: "ANALYZING", label: "Business Insights (Value Prop)" },
    { id: "SAVING", label: "CRM Sync & Lead Scoring" },
    { id: "EMAIL_PREPARATION", label: "Email Agent (Contextual Draft)" },
    { id: "COMPLETED", label: "Workflow Completed" },
  ];

  const handleLaunch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!targetUrl.trim()) return;

    setRunning(true);
    setError(null);
    setResult(null);
    setActiveStepId("VALIDATING");
    setCompletedStepIds([]);
    setElapsedSeconds(0);

    const timer = setInterval(() => {
      setElapsedSeconds((prev) => prev + 1);
    }, 1000);

    const poller = setInterval(async () => {
      try {
        const runs = await api.getResearchRuns(1, 1);
        if (runs.items && runs.items.length > 0) {
          const latest = runs.items[0];
          if (latest.status) {
            setActiveStepId(latest.status);
          }
          if (latest.checkpoints) {
            setCompletedStepIds(latest.checkpoints.map((c: any) => c.state));
          }
        }
      } catch {}
    }, 1200);

    try {
      const res = await api.startResearchRun(targetUrl.trim(), crawlDepth, maxPages, includeEmail);
      setResult(res);
      setActiveStepId("COMPLETED");
      setCompletedStepIds(workflowSteps.map((s) => s.id));
    } catch (err: any) {
      setError(err.message || "Execution error");
    } finally {
      clearInterval(timer);
      clearInterval(poller);
      setRunning(false);
    }
  };

  return (
    <div className="p-8 max-w-5xl mx-auto space-y-8">
      {/* Header */}
      <div>
        <h2 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
          <Bot className="w-5 h-5 text-indigo-400" />
          <span>Multi-Agent Research Console</span>
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Coordinate specialized AI agents to discover, extract, verify citations, score leads, and generate personalized email drafts.
        </p>
      </div>

      {/* Input Configuration Box */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6 shadow-sm">
        <form onSubmit={handleLaunch} className="space-y-4">
          <div>
            <label className="text-xs font-semibold text-slate-200 block mb-1.5">
              Target Company Website or Domain URL
            </label>
            <div className="relative">
              <input
                type="text"
                value={targetUrl}
                onChange={(e) => setTargetUrl(e.target.value)}
                placeholder="https://example.com"
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-4 py-2.5 text-xs text-slate-200 font-mono focus:outline-none focus:border-indigo-500"
                disabled={running}
                required
              />
            </div>
            <p className="text-[11px] text-slate-500 mt-1">
              Protected by SSRF firewall blocking private subnets, cloud metadata, and malicious redirects.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2">
            <div>
              <label className="text-[11px] font-semibold text-slate-300 block mb-1">
                Crawl Depth (Levels)
              </label>
              <select
                value={crawlDepth}
                onChange={(e) => setCrawlDepth(Number(e.target.value))}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                disabled={running}
              >
                <option value={1}>1 (Seed page only)</option>
                <option value={2}>2 (Recommended)</option>
                <option value={3}>3 (Deep crawl)</option>
              </select>
            </div>

            <div>
              <label className="text-[11px] font-semibold text-slate-300 block mb-1">
                Max Pages to Scrape
              </label>
              <select
                value={maxPages}
                onChange={(e) => setMaxPages(Number(e.target.value))}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                disabled={running}
              >
                <option value={5}>5 pages</option>
                <option value={15}>15 pages (Standard)</option>
                <option value={30}>30 pages (Thorough)</option>
              </select>
            </div>

            <div className="flex items-center gap-2 pt-6">
              <input
                type="checkbox"
                id="emailGen"
                checked={includeEmail}
                onChange={(e) => setIncludeEmail(e.target.checked)}
                className="rounded bg-slate-950 border-slate-800 text-indigo-600 focus:ring-0"
                disabled={running}
              />
              <label htmlFor="emailGen" className="text-xs text-slate-300 select-none">
                Draft Email if Qualified
              </label>
            </div>
          </div>

          <button
            type="submit"
            disabled={running}
            className="w-full mt-4 flex items-center justify-center gap-2 py-3 px-4 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-medium text-xs transition-colors shadow-sm"
          >
            {running ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Autonomous Agents Executing...</span>
              </>
            ) : (
              <>
                <Play className="w-4 h-4 fill-white" />
                <span>Launch Multi-Agent Pipeline</span>
              </>
            )}
          </button>
        </form>
      </div>

      {/* Error Notice */}
      {error && (
        <div className="p-4 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs flex items-center gap-3">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Execution Tracker & Progress */}
      {running && (
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300">
                Agent State Machine In-Flight
              </h3>
              <p className="text-[11px] text-slate-500 mt-0.5">
                Multi-agent orchestration in progress ({elapsedSeconds}s elapsed)
              </p>
            </div>
            <span className="flex items-center gap-1.5 text-xs text-indigo-400 font-mono bg-indigo-500/10 border border-indigo-500/20 px-2.5 py-1 rounded-full">
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
              <span>{activeStepId}...</span>
            </span>
          </div>

          <div className="space-y-1.5">
            {workflowSteps.map((s, idx) => {
              const isCompleted = completedStepIds.includes(s.id) || (result && result.status === "COMPLETED");
              const isCurrent = activeStepId === s.id && !isCompleted;
              return (
                <div
                  key={s.id}
                  className={`flex items-center justify-between text-xs py-2 px-3 rounded-lg border transition-all ${
                    isCurrent
                      ? "bg-indigo-950/40 border-indigo-500/40 text-indigo-200 shadow-sm"
                      : isCompleted
                      ? "bg-slate-950/40 border-emerald-500/20 text-slate-300"
                      : "border-transparent text-slate-500"
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <span
                      className={`w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-mono font-bold ${
                        isCompleted
                          ? "bg-emerald-500/20 text-emerald-400"
                          : isCurrent
                          ? "bg-indigo-600 text-white animate-pulse"
                          : "bg-slate-800 text-slate-500"
                      }`}
                    >
                      {isCompleted ? <CheckCircle2 className="w-3.5 h-3.5" /> : idx + 1}
                    </span>
                    <span className={isCurrent ? "font-semibold text-white" : isCompleted ? "text-slate-200" : ""}>
                      {s.label}
                    </span>
                  </div>
                  {isCurrent && (
                    <span className="flex items-center gap-1 text-[11px] text-indigo-400 font-mono">
                      <Loader2 className="w-3 h-3 animate-spin" />
                      <span>In-Flight</span>
                    </span>
                  )}
                  {isCompleted && (
                    <span className="text-[10px] text-emerald-400 font-mono font-medium">Done</span>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Results Card */}
      {result && (
        <div className="bg-slate-900/80 border border-emerald-500/30 rounded-xl p-6 space-y-6 shadow-lg shadow-emerald-950/20">
          <div className="flex items-center justify-between pb-4 border-b border-slate-800">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center">
                <CheckCircle2 className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-white">
                  Intelligence Gathered: {result.company_name || targetUrl}
                </h3>
                <p className="text-xs text-slate-400 font-mono">Run ID: {result.run_id}</p>
              </div>
            </div>

            {result.company_id && (
              <button
                onClick={() => onSelectCompany(result.company_id)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold"
              >
                <span>View Company Profile</span>
                <ExternalLink className="w-3.5 h-3.5" />
              </button>
            )}
          </div>

          {/* Quick Metrics */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
              <p className="text-[10px] text-slate-400 uppercase font-semibold">Lead Score</p>
              <p className="text-xl font-bold text-indigo-400 mt-1">{result.lead_score ?? 0}/100</p>
            </div>
            <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
              <p className="text-[10px] text-slate-400 uppercase font-semibold">Status</p>
              <p className="text-xl font-bold text-emerald-400 mt-1">{result.status}</p>
            </div>
            <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
              <p className="text-[10px] text-slate-400 uppercase font-semibold">Execution Time</p>
              <p className="text-xl font-bold text-slate-200 mt-1">{result.total_duration_ms}ms</p>
            </div>
            <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
              <p className="text-[10px] text-slate-400 uppercase font-semibold">AI Token Cost</p>
              <p className="text-xl font-bold text-slate-200 mt-1">${result.total_cost_usd}</p>
            </div>
          </div>

          {/* Email Draft Notice */}
          {result.email_draft_id && (
            <div className="p-4 rounded-lg bg-amber-500/10 border border-amber-500/20 text-xs text-amber-300 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Zap className="w-4 h-4 text-amber-400" />
                <span>
                  Personalized outreach email drafted and placed in <strong>Approval Queue</strong>.
                </span>
              </div>
              <span className="font-mono text-[10px] bg-amber-500/20 px-2 py-0.5 rounded">
                Pending Approval
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
