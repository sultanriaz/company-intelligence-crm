import React, { useEffect, useState } from "react";
import { MailCheck, Check, X, ShieldAlert, Sparkles, Send, Loader2 } from "lucide-react";
import { api } from "../api/client";
import { EmailDraft } from "../types";

export const ApprovalQueuePage: React.FC = () => {
  const [drafts, setDrafts] = useState<EmailDraft[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedDraft, setSelectedDraft] = useState<EmailDraft | null>(null);
  const [decisionFeedback, setDecisionFeedback] = useState("");
  const [processing, setProcessing] = useState(false);
  const [actionNotice, setActionNotice] = useState<string | null>(null);

  useEffect(() => {
    loadDrafts();
  }, []);

  const loadDrafts = async () => {
    setLoading(true);
    try {
      const res = await api.getEmailDrafts("PENDING_APPROVAL");
      setDrafts(res);
      if (res.length > 0 && !selectedDraft) {
        setSelectedDraft(res[0]);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleDecision = async (decision: "APPROVED" | "REJECTED") => {
    if (!selectedDraft) return;
    setProcessing(true);
    setActionNotice(null);

    try {
      const res = await api.decideApproval(selectedDraft.id, decision, decisionFeedback);
      setActionNotice(
        decision === "APPROVED"
          ? `Dispatched via ${res.provider} (${res.delivery_status}). Message ID: ${res.provider_message_id || res.message_id}`
          : "Draft rejected."
      );
      setDecisionFeedback("");
      await loadDrafts();
      if (drafts.length <= 1) {
        setSelectedDraft(null);
      }
    } catch (err: any) {
      setActionNotice(`Error: ${err.message}`);
    } finally {
      setProcessing(false);
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      <div>
        <h2 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
          <MailCheck className="w-5 h-5 text-indigo-400" />
          <span>Outbound Email Approval Queue</span>
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Mandatory human verification gate. AI-generated cold outreach drafts require review before dispatch.
        </p>
      </div>

      {actionNotice && (
        <div className="p-4 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-xs font-mono">
          {actionNotice}
        </div>
      )}

      {loading ? (
        <div className="py-12 text-center text-slate-500 animate-pulse">Loading approval queue...</div>
      ) : drafts.length === 0 ? (
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-12 text-center space-y-3">
          <div className="w-10 h-10 rounded-full bg-emerald-500/10 text-emerald-400 flex items-center justify-center mx-auto">
            <Check className="w-5 h-5" />
          </div>
          <h3 className="text-sm font-semibold text-white">Approval Queue is Clear</h3>
          <p className="text-xs text-slate-400 max-w-md mx-auto">
            All generated cold outreach drafts have been approved or rejected.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Drafts List */}
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 divide-y divide-slate-800/60 max-h-[calc(100vh-14rem)] overflow-y-auto">
            <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-3 px-2">
              Pending Drafts ({drafts.length})
            </p>
            {drafts.map((d) => (
              <div
                key={d.id}
                onClick={() => setSelectedDraft(d)}
                className={`p-3 rounded-lg cursor-pointer transition-colors ${
                  selectedDraft?.id === d.id ? "bg-indigo-600/10 border border-indigo-500/30" : "hover:bg-slate-800/30"
                }`}
              >
                <p className="text-xs font-semibold text-slate-200 truncate">{d.subject}</p>
                <div className="flex items-center justify-between text-[11px] text-slate-400 mt-1">
                  <span>To: {d.contact ? `${d.contact.first_name} ${d.contact.last_name}` : "Team"}</span>
                  <span className="font-mono text-[10px] text-amber-400">Review</span>
                </div>
              </div>
            ))}
          </div>

          {/* Review Details Pane */}
          {selectedDraft && (
            <div className="lg:col-span-2 bg-slate-900/60 border border-slate-800 rounded-xl p-6 flex flex-col justify-between space-y-6">
              <div className="space-y-4">
                {/* Draft Metadata */}
                <div className="pb-4 border-b border-slate-800 space-y-2">
                  <div className="flex justify-between items-start">
                    <div>
                      <span className="text-[10px] uppercase font-bold text-slate-500">Subject</span>
                      <h3 className="text-base font-bold text-white mt-0.5">{selectedDraft.subject}</h3>
                    </div>
                    <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">
                      Pending Human Gate
                    </span>
                  </div>

                  <div className="flex flex-wrap gap-4 text-xs text-slate-400 font-mono">
                    <span>Recipient: {selectedDraft.contact?.email || "Unknown"}</span>
                    <span>•</span>
                    <span>Created: {new Date(selectedDraft.created_at).toLocaleTimeString()}</span>
                  </div>

                  {selectedDraft.referenced_facts && (
                    <div className="flex items-center gap-1.5 pt-1">
                      <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
                      <span className="text-[11px] text-indigo-300">
                        Referenced verified facts: {selectedDraft.referenced_facts}
                      </span>
                    </div>
                  )}
                </div>

                {/* Email Content Preview */}
                <div className="bg-slate-950 border border-slate-800 rounded-lg p-5">
                  <p className="text-[10px] uppercase font-bold text-slate-500 mb-2 font-mono">Email Body (Plain Text)</p>
                  <pre className="text-xs text-slate-300 whitespace-pre-wrap font-sans leading-relaxed">
                    {selectedDraft.body_text}
                  </pre>
                </div>

                {/* Reviewer Feedback Notes */}
                <div>
                  <label className="text-[11px] font-semibold text-slate-400 block mb-1">
                    Reviewer Feedback / Revision Notes (Optional)
                  </label>
                  <input
                    type="text"
                    value={decisionFeedback}
                    onChange={(e) => setDecisionFeedback(e.target.value)}
                    placeholder="e.g., Looks great, verified against public site."
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                    disabled={processing}
                  />
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
                <button
                  onClick={() => handleDecision("REJECTED")}
                  disabled={processing}
                  className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-rose-400 hover:text-rose-300 text-xs font-semibold transition-colors disabled:opacity-50"
                >
                  <X className="w-4 h-4" />
                  <span>Reject Draft</span>
                </button>

                <button
                  onClick={() => handleDecision("APPROVED")}
                  disabled={processing}
                  className="flex items-center gap-1.5 px-5 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-sm transition-colors disabled:opacity-50"
                >
                  {processing ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span>Dispatching Outbox...</span>
                    </>
                  ) : (
                    <>
                      <Send className="w-4 h-4" />
                      <span>Approve & Send Email</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
