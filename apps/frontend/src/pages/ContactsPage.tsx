import React, { useEffect, useState } from "react";
import { Users, Mail, Phone, ExternalLink, ShieldAlert, CheckCircle2 } from "lucide-react";
import { api } from "../api/client";
import { Contact } from "../types";

export const ContactsPage: React.FC = () => {
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);

  useEffect(() => {
    loadContacts();
  }, [page]);

  const loadContacts = async () => {
    setLoading(true);
    try {
      const res = await api.getContacts(page, 20);
      setContacts(res.items);
      setTotalCount(res.total);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      <div>
        <h2 className="text-xl font-bold text-white tracking-tight">Contact Directory</h2>
        <p className="text-xs text-slate-400">Total {totalCount} discovered business contacts</p>
      </div>

      <div className="bg-slate-900/60 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
        <table className="w-full text-left text-xs text-slate-300">
          <thead className="bg-slate-950/60 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-800">
            <tr>
              <th className="py-3 px-4">Contact</th>
              <th className="py-3 px-4">Title</th>
              <th className="py-3 px-4">Email</th>
              <th className="py-3 px-4">Phone</th>
              <th className="py-3 px-4">Permission Status</th>
              <th className="py-3 px-4">Suppression</th>
              <th className="py-3 px-4">Provenance</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/40">
            {loading ? (
              <tr>
                <td colSpan={7} className="py-8 text-center text-slate-500">Loading contacts...</td>
              </tr>
            ) : contacts.length === 0 ? (
              <tr>
                <td colSpan={7} className="py-8 text-center text-slate-500">No contacts discovered yet.</td>
              </tr>
            ) : (
              contacts.map((c) => (
                <tr key={c.id} className="hover:bg-slate-800/20">
                  <td className="py-3.5 px-4 font-semibold text-slate-100">
                    {c.first_name} {c.last_name}
                  </td>
                  <td className="py-3.5 px-4 text-slate-300">{c.title || "—"}</td>
                  <td className="py-3.5 px-4 font-mono text-slate-200">{c.email}</td>
                  <td className="py-3.5 px-4 text-slate-400">{c.phone || "—"}</td>
                  <td className="py-3.5 px-4">
                    <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-indigo-500/10 text-indigo-400">
                      {c.permission_status}
                    </span>
                  </td>
                  <td className="py-3.5 px-4">
                    {c.is_suppressed ? (
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-500/10 text-rose-400 border border-rose-500/20">
                        Suppressed
                      </span>
                    ) : (
                      <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-500/10 text-emerald-400">
                        Eligible
                      </span>
                    )}
                  </td>
                  <td className="py-3.5 px-4">
                    {c.provenance_url ? (
                      <a
                        href={c.provenance_url}
                        target="_blank"
                        rel="noreferrer"
                        className="text-xs text-indigo-400 hover:text-indigo-300 flex items-center gap-1 font-mono"
                      >
                        <span>source</span>
                        <ExternalLink className="w-3 h-3" />
                      </a>
                    ) : (
                      <span className="text-slate-500">—</span>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
