import React, { useEffect, useState } from "react";
import { KanbanSquare, Building2, ExternalLink } from "lucide-react";
import { api } from "../api/client";
import { CRMPipeline, Company } from "../types";

interface PipelinePageProps {
  onSelectCompany: (id: string) => void;
}

export const PipelinePage: React.FC<PipelinePageProps> = ({ onSelectCompany }) => {
  const [pipeline, setPipeline] = useState<CRMPipeline | null>(null);
  const [companies, setCompanies] = useState<Company[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadPipelineData();
  }, []);

  const loadPipelineData = async () => {
    setLoading(true);
    try {
      const [pipeRes, compRes] = await Promise.all([
        api.getPipelines(),
        api.getCompanies(1, 100),
      ]);
      if (pipeRes && pipeRes.length > 0) {
        setPipeline(pipeRes[0]);
      }
      setCompanies(compRes.items || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="p-8 text-center text-slate-500 animate-pulse">Loading sales pipeline...</div>;
  }

  if (!pipeline) {
    return <div className="p-8 text-center text-slate-500">No CRM pipeline defined.</div>;
  }

  return (
    <div className="p-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight">{pipeline.name}</h2>
          <p className="text-xs text-slate-400">Kanban sales progression for qualified leads</p>
        </div>
      </div>

      {/* Kanban Columns */}
      <div className="flex gap-4 overflow-x-auto pb-6">
        {pipeline.stages.map((stage) => {
          const stageCompanies = companies.filter((c) => c.pipeline_stage_id === stage.id);
          return (
            <div
              key={stage.id}
              className="w-72 shrink-0 bg-slate-900/60 border border-slate-800 rounded-xl p-4 flex flex-col max-h-[calc(100vh-14rem)]"
            >
              {/* Stage Header */}
              <div className="flex items-center justify-between pb-3 border-b border-slate-800/80 mb-3">
                <div className="flex items-center gap-2">
                  <div
                    className="w-2.5 h-2.5 rounded-full"
                    style={{ backgroundColor: stage.color || "#6366f1" }}
                  />
                  <h3 className="text-xs font-bold text-slate-200 tracking-tight">{stage.name}</h3>
                </div>
                <span className="text-xs font-mono font-semibold px-2 py-0.5 rounded bg-slate-800 text-slate-400">
                  {stageCompanies.length}
                </span>
              </div>

              {/* Cards Container */}
              <div className="flex-1 overflow-y-auto space-y-2.5 pr-1">
                {stageCompanies.length === 0 ? (
                  <div className="py-8 text-center text-[11px] text-slate-600 border border-dashed border-slate-800/60 rounded-lg">
                    No leads in this stage
                  </div>
                ) : (
                  stageCompanies.map((c) => (
                    <div
                      key={c.id}
                      onClick={() => onSelectCompany(c.id)}
                      className="p-3 bg-slate-950/80 border border-slate-800 hover:border-indigo-500/50 rounded-lg cursor-pointer transition-all shadow-sm hover:shadow-indigo-500/10 group"
                    >
                      <div className="flex items-start justify-between gap-2">
                        <p className="text-xs font-bold text-slate-200 group-hover:text-indigo-400 transition-colors">
                          {c.name}
                        </p>
                        {c.total_score !== undefined && (
                          <span
                            className={`text-[10px] font-extrabold px-1.5 py-0.5 rounded ${
                              c.total_score >= 60 ? "bg-emerald-500/10 text-emerald-400" : "bg-amber-500/10 text-amber-400"
                            }`}
                          >
                            {c.total_score}
                          </span>
                        )}
                      </div>

                      <p className="text-[11px] font-mono text-slate-400 mt-1">{c.primary_domain}</p>
                      <p className="text-[11px] text-slate-500 mt-1 truncate">{c.industry || "General Industry"}</p>
                    </div>
                  ))
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
