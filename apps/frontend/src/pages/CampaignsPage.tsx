import React, { useEffect, useState } from "react";
import { Send, Plus, CheckCircle2, Pause, Play, AlertCircle } from "lucide-react";
import { api } from "../api/client";
import { Campaign } from "../types";

export const CampaignsPage: React.FC = () => {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [loading, setLoading] = useState(true);
  const [newCampaignName, setNewCampaignName] = useState("");
  const [dailyLimit, setDailyLimit] = useState(50);
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    loadCampaigns();
  }, []);

  const loadCampaigns = async () => {
    setLoading(true);
    try {
      const res = await api.getCampaigns();
      setCampaigns(res);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newCampaignName.trim()) return;
    setCreating(true);
    try {
      await fetch("/api/v1/campaigns", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: newCampaignName.trim(), daily_limit: dailyLimit }),
      });
      setNewCampaignName("");
      await loadCampaigns();
    } catch (e) {
      console.error(e);
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      <div>
        <h2 className="text-xl font-bold text-white tracking-tight">Outbound Campaigns</h2>
        <p className="text-xs text-slate-400">Configure email outreach series, rate caps, and approval policies</p>
      </div>

      {/* Create Campaign Box */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5">
        <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider mb-3">Create New Outreach Campaign</h3>
        <form onSubmit={handleCreate} className="flex flex-col sm:flex-row gap-3">
          <input
            type="text"
            placeholder="Campaign name (e.g. Q4 Cloud AI Outreach)"
            value={newCampaignName}
            onChange={(e) => setNewCampaignName(e.target.value)}
            className="flex-1 bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
            required
          />
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400">Daily Cap:</span>
            <input
              type="number"
              min="1"
              max="500"
              value={dailyLimit}
              onChange={(e) => setDailyLimit(Number(e.target.value))}
              className="w-20 bg-slate-950 border border-slate-800 rounded-lg px-2 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500 font-mono"
            />
          </div>
          <button
            type="submit"
            disabled={creating}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white rounded-lg text-xs font-semibold shrink-0"
          >
            {creating ? "Creating..." : "Create Campaign"}
          </button>
        </form>
      </div>

      {/* Campaigns Table */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
        <table className="w-full text-left text-xs text-slate-300">
          <thead className="bg-slate-950/60 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-800">
            <tr>
              <th className="py-3 px-4">Campaign Name</th>
              <th className="py-3 px-4">Status</th>
              <th className="py-3 px-4">Daily Sending Limit</th>
              <th className="py-3 px-4">Auto-Send Permitted</th>
              <th className="py-3 px-4">Created Date</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/40">
            {loading ? (
              <tr>
                <td colSpan={5} className="py-8 text-center text-slate-500">Loading campaigns...</td>
              </tr>
            ) : campaigns.length === 0 ? (
              <tr>
                <td colSpan={5} className="py-8 text-center text-slate-500">No campaigns created yet.</td>
              </tr>
            ) : (
              campaigns.map((c) => (
                <tr key={c.id} className="hover:bg-slate-800/20">
                  <td className="py-3.5 px-4 font-semibold text-slate-100">{c.name}</td>
                  <td className="py-3.5 px-4">
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-500/10 text-indigo-400">
                      {c.status}
                    </span>
                  </td>
                  <td className="py-3.5 px-4 font-mono text-slate-300">{c.daily_limit} emails/day</td>
                  <td className="py-3.5 px-4 text-slate-400">
                    {c.auto_send_enabled ? "Enabled" : "Manual Approval Required"}
                  </td>
                  <td className="py-3.5 px-4 text-slate-400">{new Date(c.created_at).toLocaleDateString()}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
