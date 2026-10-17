import React, { useEffect, useState } from "react";
import { ArrowLeft, ExternalLink, ShieldCheck, Award, Layers, Users, History, CheckCircle2 } from "lucide-react";
import { api } from "../api/client";
import { CompanyDetail, LeadScore } from "../types";

interface CompanyDetailPageProps {
  companyId: string;
  onBack: () => void;
}

export const CompanyDetailPage: React.FC<CompanyDetailPageProps> = ({ companyId, onBack }) => {
  const [company, setCompany] = useState<CompanyDetail | null>(null);
  const [leadScore, setLeadScore] = useState<LeadScore | null>(null);
  const [activities, setActivities] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadCompanyDetails();
  }, [companyId]);

  const loadCompanyDetails = async () => {
    setLoading(true);
    try {
      const [compRes, scoreRes, actRes] = await Promise.all([
        api.getCompany(companyId),
        api.getLeadScore(companyId).catch(() => null),
        api.getCompanyActivities(companyId).catch(() => []),
      ]);
      setCompany(compRes);
      setLeadScore(scoreRes);
      setActivities(actRes || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="p-8 text-center text-slate-500">
        <p className="animate-pulse">Loading company intelligence profile...</p>
      </div>
    );
  }

  if (!company) {
    return (
      <div className="p-8 max-w-4xl mx-auto space-y-4">
        <button onClick={onBack} className="text-xs text-indigo-400 flex items-center gap-1">
          <ArrowLeft className="w-4 h-4" /> Back to Directory
        </button>
        <p className="text-slate-400">Company not found.</p>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      {/* Top Navigation */}
      <button
        onClick={onBack}
        className="flex items-center gap-1.5 text-xs font-semibold text-slate-400 hover:text-slate-200 transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        <span>Back to Companies</span>
      </button>

      {/* Header Profile Card */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6 flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="flex items-center gap-4">
          <div className="w-14 h-14 rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-500 flex items-center justify-center text-white font-bold text-lg shadow-md">
            {company.name.slice(0, 2).toUpperCase()}
          </div>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-xl font-bold text-white tracking-tight">{company.name}</h1>
              <span
                className={`px-2.5 py-0.5 rounded-full text-xs font-bold ${
                  company.status === "QUALIFIED"
                    ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                    : "bg-slate-800 text-slate-300"
                }`}
              >
                {company.status}
              </span>
            </div>
            <div className="flex flex-wrap items-center gap-4 mt-1 text-xs text-slate-400">
              <a
                href={`https://${company.primary_domain}`}
                target="_blank"
                rel="noreferrer"
                className="hover:text-indigo-400 flex items-center gap-1 font-mono"
              >
                <span>{company.primary_domain}</span>
                <ExternalLink className="w-3 h-3" />
              </a>
              <span>•</span>
              <span>{company.industry || "General Industry"}</span>
              <span>•</span>
              <span>{company.headquarters || "Global"}</span>
              <span>•</span>
              <span>{company.employee_range || "Unknown Scale"}</span>
            </div>
          </div>
        </div>

        {/* Lead Score Widget */}
        {leadScore && (
          <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-4 flex items-center gap-4 shrink-0">
            <div className="text-center">
              <span className="text-3xl font-extrabold text-indigo-400 tracking-tight">
                {leadScore.total_score}
              </span>
              <span className="text-xs text-slate-500 block font-medium">/ 100</span>
            </div>
            <div className="border-l border-slate-800 pl-4">
              <p className="text-xs font-bold text-white">Lead Score</p>
              <p className="text-[11px] text-slate-400">
                {leadScore.is_qualified ? "Target Qualified" : "Prospect Stage"}
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Grid: Left Column (Intelligence & Facts), Right Column (Lead Scoring & Timeline) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Facts & Executive Summary */}
        <div className="lg:col-span-2 space-y-6">
          {/* Executive Summary & Research Report */}
          {company.reports && company.reports.length > 0 && (
            <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6 space-y-4">
              <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                <Layers className="w-4 h-4 text-indigo-400" />
                <span>Executive Intelligence Report</span>
              </h3>
              <p className="text-xs text-slate-300 leading-relaxed">
                {company.reports[0].executive_summary}
              </p>

              {company.reports[0].opportunities && (
                <div className="mt-4 pt-4 border-t border-slate-800">
                  <h4 className="text-xs font-semibold text-slate-200 uppercase tracking-wider mb-2">
                    Market Opportunities
                  </h4>
                  <ul className="list-disc list-inside text-xs text-slate-400 space-y-1">
                    {JSON.parse(company.reports[0].opportunities).map((opp: string, i: number) => (
                      <li key={i}>{opp}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {/* Verified Facts & Citations */}
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-emerald-400" />
                <span>Verified Facts & Citations</span>
              </h3>
              <span className="text-xs text-slate-500 font-mono">{company.facts.length} citations</span>
            </div>

            <div className="mt-4 divide-y divide-slate-800/40">
              {company.facts.length === 0 ? (
                <p className="text-xs text-slate-500 py-4 text-center">No research facts recorded.</p>
              ) : (
                company.facts.map((f) => (
                  <div key={f.id} className="py-3 flex flex-col sm:flex-row sm:items-baseline justify-between gap-2">
                    <div>
                      <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
                        {f.field_name}
                      </span>
                      <p className="text-xs text-slate-200 mt-0.5">{f.field_value}</p>
                    </div>

                    <div className="flex items-center gap-3 shrink-0">
                      <span className="text-[11px] font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                        {Math.round(f.confidence_score * 100)}% conf
                      </span>
                      <a
                        href={f.source_url}
                        target="_blank"
                        rel="noreferrer"
                        className="text-xs text-indigo-400 hover:text-indigo-300 flex items-center gap-1 font-mono"
                      >
                        <span>source</span>
                        <ExternalLink className="w-3 h-3" />
                      </a>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Right Column: Score Breakdown & Activity */}
        <div className="space-y-6">
          {/* Transparent Score Breakdown */}
          {leadScore && (
            <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6">
              <h3 className="text-sm font-semibold text-white flex items-center gap-2 pb-3 border-b border-slate-800">
                <Award className="w-4 h-4 text-indigo-400" />
                <span>Score Breakdown Rationale</span>
              </h3>

              <div className="mt-4 space-y-4">
                {leadScore.explanations.map((exp) => (
                  <div key={exp.dimension} className="space-y-1">
                    <div className="flex justify-between text-xs">
                      <span className="font-medium text-slate-300 capitalize">
                        {exp.dimension.replace("_", " ")}
                      </span>
                      <span className="font-bold text-indigo-400">
                        {exp.score_assigned}/{exp.max_score}
                      </span>
                    </div>
                    <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                      <div
                        className="bg-indigo-500 h-1.5 rounded-full"
                        style={{ width: `${(exp.score_assigned / exp.max_score) * 100}%` }}
                      />
                    </div>
                    <p className="text-[11px] text-slate-400">{exp.reason}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* CRM Activity Timeline */}
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6">
            <h3 className="text-sm font-semibold text-white flex items-center gap-2 pb-3 border-b border-slate-800">
              <History className="w-4 h-4 text-slate-400" />
              <span>CRM Activity Timeline</span>
            </h3>

            <div className="mt-4 space-y-3">
              {activities.length === 0 ? (
                <p className="text-xs text-slate-500 text-center py-4">No logged activities.</p>
              ) : (
                activities.map((a) => (
                  <div key={a.id} className="text-xs border-l-2 border-indigo-500/40 pl-3 py-1 space-y-0.5">
                    <div className="flex items-center justify-between text-slate-400 text-[10px]">
                      <span className="font-semibold text-indigo-400">{a.activity_type}</span>
                      <span>{new Date(a.created_at).toLocaleDateString()}</span>
                    </div>
                    <p className="text-slate-200">{a.details}</p>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
