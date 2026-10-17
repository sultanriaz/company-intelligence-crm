import React, { useEffect, useState } from "react";
import { ShieldBan, Plus, Trash2 } from "lucide-react";
import { api } from "../api/client";
import { EmailSuppression } from "../types";

export const SuppressionPage: React.FC = () => {
  const [suppressions, setSuppressions] = useState<EmailSuppression[]>([]);
  const [loading, setLoading] = useState(true);
  const [newEmail, setNewEmail] = useState("");
  const [reason, setReason] = useState("MANUAL");

  useEffect(() => {
    loadSuppressions();
  }, []);

  const loadSuppressions = async () => {
    setLoading(true);
    try {
      const res = await api.getSuppressions();
      setSuppressions(res);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newEmail.trim()) return;
    try {
      await api.addSuppression(newEmail.trim(), reason);
      setNewEmail("");
      await loadSuppressions();
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      <div>
        <h2 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
          <ShieldBan className="w-5 h-5 text-rose-400" />
          <span>Email Suppression List</span>
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Guaranteed global opt-out enforcement. Blocked recipients are rejected before any outbound email reaches provider APIs.
        </p>
      </div>

      {/* Add to suppression list form */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5">
        <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider mb-3">Add Recipient to Suppression List</h3>
        <form onSubmit={handleAdd} className="flex flex-col sm:flex-row gap-3">
          <input
            type="email"
            placeholder="recipient@example.com"
            value={newEmail}
            onChange={(e) => setNewEmail(e.target.value)}
            className="flex-1 bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500 font-mono"
            required
          />
          <select
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
          >
            <option value="MANUAL">Manual Suppression</option>
            <option value="UNSUBSCRIBE">Unsubscribe Request</option>
            <option value="BOUNCE">Hard Bounce</option>
            <option value="COMPLAINT">Spam Complaint</option>
          </select>
          <button
            type="submit"
            className="px-4 py-2 bg-rose-600 hover:bg-rose-500 text-white rounded-lg text-xs font-semibold shrink-0"
          >
            Add to Suppression List
          </button>
        </form>
      </div>

      {/* Suppression Table */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
        <table className="w-full text-left text-xs text-slate-300">
          <thead className="bg-slate-950/60 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-800">
            <tr>
              <th className="py-3 px-4">Suppressed Email Address</th>
              <th className="py-3 px-4">Reason</th>
              <th className="py-3 px-4">Enforcement Date</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/40">
            {loading ? (
              <tr>
                <td colSpan={3} className="py-8 text-center text-slate-500">Loading suppression list...</td>
              </tr>
            ) : suppressions.length === 0 ? (
              <tr>
                <td colSpan={3} className="py-8 text-center text-slate-500">No emails on the suppression list.</td>
              </tr>
            ) : (
              suppressions.map((s) => (
                <tr key={s.id} className="hover:bg-slate-800/20">
                  <td className="py-3.5 px-4 font-mono font-medium text-slate-200">{s.email}</td>
                  <td className="py-3.5 px-4">
                    <span className="px-2.5 py-0.5 rounded text-[10px] font-bold bg-rose-500/10 text-rose-400 border border-rose-500/20">
                      {s.reason}
                    </span>
                  </td>
                  <td className="py-3.5 px-4 text-slate-400">{new Date(s.created_at).toLocaleString()}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
