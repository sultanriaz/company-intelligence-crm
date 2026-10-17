import React, { useEffect, useState } from "react";
import { ScrollText, Shield } from "lucide-react";
import { api } from "../api/client";
import { AuditLog } from "../types";

export const AuditLogsPage: React.FC = () => {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadAuditLogs();
  }, []);

  const loadAuditLogs = async () => {
    setLoading(true);
    try {
      const res = await api.getAuditLogs();
      setLogs(res);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      <div>
        <h2 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
          <ScrollText className="w-5 h-5 text-indigo-400" />
          <span>Security & Audit Trails</span>
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Tamper-evident log of administrative actions, webhook ingestion, and state changes.
        </p>
      </div>

      <div className="bg-slate-900/60 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
        <table className="w-full text-left text-xs text-slate-300">
          <thead className="bg-slate-950/60 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-800">
            <tr>
              <th className="py-3 px-4">Timestamp</th>
              <th className="py-3 px-4">Action</th>
              <th className="py-3 px-4">Resource Type</th>
              <th className="py-3 px-4">Details</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/40">
            {loading ? (
              <tr>
                <td colSpan={4} className="py-8 text-center text-slate-500">Loading audit trails...</td>
              </tr>
            ) : logs.length === 0 ? (
              <tr>
                <td colSpan={4} className="py-8 text-center text-slate-500">No audit events recorded yet.</td>
              </tr>
            ) : (
              logs.map((l) => (
                <tr key={l.id} className="hover:bg-slate-800/20">
                  <td className="py-3.5 px-4 font-mono text-slate-400">{new Date(l.timestamp).toLocaleString()}</td>
                  <td className="py-3.5 px-4 font-semibold text-slate-200">{l.action}</td>
                  <td className="py-3.5 px-4 font-mono text-indigo-400">{l.resource_type}</td>
                  <td className="py-3.5 px-4 text-slate-300 max-w-md truncate">{l.details || "—"}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
