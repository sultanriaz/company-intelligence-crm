import React, { useState } from "react";
import { Settings, Key, Send, CheckCircle2, AlertCircle } from "lucide-react";
import { api } from "../api/client";

export const SettingsPage: React.FC = () => {
  const [providerType, setProviderType] = useState("resend");
  const [apiKey, setApiKey] = useState("");
  const [testEmail, setTestEmail] = useState("test@company-intelligence.local");
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  const handleSaveCredential = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!apiKey.trim()) return;
    try {
      await fetch("/api/v1/integrations", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          provider_type: providerType,
          secret_key: apiKey.trim(),
          is_enabled: true,
        }),
      });
      setStatusMessage(`Credential for ${providerType.toUpperCase()} encrypted and saved successfully.`);
      setApiKey("");
    } catch (err: any) {
      setStatusMessage(`Error saving credential: ${err.message}`);
    }
  };

  const handleSendTest = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!testEmail.trim()) return;
    try {
      const res = await api.sendTestEmail(testEmail.trim());
      setStatusMessage(`Test email dispatched via ${res.provider} (${res.status}). Message ID: ${res.message_id || "mock"}`);
    } catch (err: any) {
      setStatusMessage(`Error sending test: ${err.message}`);
    }
  };

  return (
    <div className="p-8 max-w-4xl mx-auto space-y-8">
      <div>
        <h2 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
          <Settings className="w-5 h-5 text-indigo-400" />
          <span>System & Integration Settings</span>
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Manage AES-256 encrypted provider credentials, test deliverability sandbox, and webhook configurations.
        </p>
      </div>

      {statusMessage && (
        <div className="p-4 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-xs font-mono">
          {statusMessage}
        </div>
      )}

      {/* Encrypted Credentials Management */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6 space-y-4">
        <h3 className="text-sm font-semibold text-white flex items-center gap-2">
          <Key className="w-4 h-4 text-indigo-400" />
          <span>Third-Party API Credentials</span>
        </h3>
        <p className="text-xs text-slate-400">
          Credentials are encrypted with AES-GCM-256 prior to database storage.
        </p>

        <form onSubmit={handleSaveCredential} className="space-y-3 pt-2">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <select
              value={providerType}
              onChange={(e) => setProviderType(e.target.value)}
              className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
            >
              <option value="resend">Resend API Key</option>
              <option value="sendgrid">SendGrid API Key</option>
              <option value="ses">Amazon SES</option>
              <option value="openai">OpenAI API Key</option>
              <option value="anthropic">Anthropic API Key</option>
            </select>

            <input
              type="password"
              placeholder="Paste API Secret Key..."
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              className="sm:col-span-2 bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500 font-mono"
              required
            />
          </div>

          <button
            type="submit"
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-semibold"
          >
            Encrypt & Save Credential
          </button>
        </form>
      </div>

      {/* Test Sandbox Dispatch */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6 space-y-4">
        <h3 className="text-sm font-semibold text-white flex items-center gap-2">
          <Send className="w-4 h-4 text-emerald-400" />
          <span>Test Sandbox Email Dispatch</span>
        </h3>
        <p className="text-xs text-slate-400">
          Verify provider connectivity by routing a test message through the configured adapter.
        </p>

        <form onSubmit={handleSendTest} className="flex gap-3 pt-2">
          <input
            type="email"
            value={testEmail}
            onChange={(e) => setTestEmail(e.target.value)}
            className="flex-1 bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 font-mono focus:outline-none focus:border-indigo-500"
            required
          />
          <button
            type="submit"
            className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-semibold shrink-0"
          >
            Send Test Message
          </button>
        </form>
      </div>
    </div>
  );
};
