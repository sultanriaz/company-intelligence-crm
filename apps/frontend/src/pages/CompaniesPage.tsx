import React, { useEffect, useState } from "react";
import { Building2, Search, Plus, ExternalLink, Filter } from "lucide-react";
import { api } from "../api/client";
import { Company } from "../types";

interface CompaniesPageProps {
  onSelectCompany: (id: string) => void;
  onOpenResearch: () => void;
}

export const CompaniesPage: React.FC<CompaniesPageProps> = ({ onSelectCompany, onOpenResearch }) => {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);

  useEffect(() => {
    fetchCompanies();
  }, [page, statusFilter]);

  const fetchCompanies = async () => {
    setLoading(true);
    try {
      const res = await api.getCompanies(page, 15, statusFilter || undefined, search || undefined);
      setCompanies(res.items);
      setTotalPages(res.total_pages);
      setTotalCount(res.total);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchCompanies();
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      {/* Top Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight">Company Directory</h2>
          <p className="text-xs text-slate-400">Total {totalCount} enriched organizations in workspace</p>
        </div>

        <button
          onClick={onOpenResearch}
          className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-semibold shadow-sm transition-colors"
        >
          <Plus className="w-4 h-4" />
          <span>Research New Company</span>
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row items-center gap-3">
        <form onSubmit={handleSearchSubmit} className="flex-1 w-full relative">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search by company name, primary domain, or industry..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-slate-900 border border-slate-800 rounded-lg pl-9 pr-4 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
          />
        </form>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          <Filter className="w-4 h-4 text-slate-400" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-300 focus:outline-none focus:border-indigo-500"
          >
            <option value="">All Statuses</option>
            <option value="PROSPECT">Prospect</option>
            <option value="QUALIFIED">Qualified</option>
            <option value="CONTACTED">Contacted</option>
            <option value="UNQUALIFIED">Unqualified</option>
          </select>
        </div>
      </div>

      {/* Companies Table */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
        <table className="w-full text-left text-xs text-slate-300">
          <thead className="bg-slate-950/60 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-800">
            <tr>
              <th className="py-3 px-4">Company</th>
              <th className="py-3 px-4">Industry</th>
              <th className="py-3 px-4">Size</th>
              <th className="py-3 px-4">Headquarters</th>
              <th className="py-3 px-4">Lead Score</th>
              <th className="py-3 px-4">Status</th>
              <th className="py-3 px-4 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/40">
            {loading ? (
              <tr>
                <td colSpan={7} className="py-8 text-center text-slate-500">Loading companies...</td>
              </tr>
            ) : companies.length === 0 ? (
              <tr>
                <td colSpan={7} className="py-8 text-center text-slate-500">No companies found matching criteria.</td>
              </tr>
            ) : (
              companies.map((c) => (
                <tr
                  key={c.id}
                  onClick={() => onSelectCompany(c.id)}
                  className="hover:bg-slate-800/20 cursor-pointer transition-colors"
                >
                  <td className="py-3.5 px-4">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-lg bg-slate-800 flex items-center justify-center font-bold text-slate-300 text-xs">
                        {c.name.slice(0, 2).toUpperCase()}
                      </div>
                      <div>
                        <p className="font-semibold text-slate-100">{c.name}</p>
                        <p className="text-[11px] text-slate-400 font-mono">{c.primary_domain}</p>
                      </div>
                    </div>
                  </td>
                  <td className="py-3.5 px-4 text-slate-300">{c.industry || "Unknown"}</td>
                  <td className="py-3.5 px-4 text-slate-400">{c.employee_range || "Unknown"}</td>
                  <td className="py-3.5 px-4 text-slate-400">{c.headquarters || "Unknown"}</td>
                  <td className="py-3.5 px-4">
                    {c.total_score !== undefined ? (
                      <span className={`font-bold ${c.total_score >= 60 ? "text-emerald-400" : "text-amber-400"}`}>
                        {c.total_score}/100
                      </span>
                    ) : (
                      <span className="text-slate-500">—</span>
                    )}
                  </td>
                  <td className="py-3.5 px-4">
                    <span
                      className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold ${
                        c.status === "QUALIFIED"
                          ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                          : "bg-slate-800 text-slate-400 border border-slate-700"
                      }`}
                    >
                      {c.status}
                    </span>
                  </td>
                  <td className="py-3.5 px-4 text-right">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelectCompany(c.id);
                      }}
                      className="text-xs text-indigo-400 hover:text-indigo-300 font-medium"
                    >
                      View Profile
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="p-4 border-t border-slate-800 flex items-center justify-between">
            <span className="text-xs text-slate-400">Page {page} of {totalPages}</span>
            <div className="flex gap-2">
              <button
                disabled={page <= 1}
                onClick={() => setPage((p) => p - 1)}
                className="px-3 py-1 bg-slate-800 disabled:opacity-50 text-xs rounded text-slate-300 hover:bg-slate-700"
              >
                Previous
              </button>
              <button
                disabled={page >= totalPages}
                onClick={() => setPage((p) => p + 1)}
                className="px-3 py-1 bg-slate-800 disabled:opacity-50 text-xs rounded text-slate-300 hover:bg-slate-700"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
