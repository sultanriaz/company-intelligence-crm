import React from "react";
import {
  LayoutDashboard,
  Building2,
  Users,
  KanbanSquare,
  Bot,
  MailCheck,
  Send,
  ShieldBan,
  ScrollText,
  Settings,
  Sparkles,
} from "lucide-react";

interface SidebarProps {
  currentTab: string;
  onSelectTab: (tab: string) => void;
  approvalCount?: number;
}

export const Sidebar: React.FC<SidebarProps> = ({ currentTab, onSelectTab, approvalCount = 0 }) => {
  const navItems = [
    { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
    { id: "companies", label: "Companies", icon: Building2 },
    { id: "contacts", label: "Contacts", icon: Users },
    { id: "pipeline", label: "Sales Pipeline", icon: KanbanSquare },
    { id: "research", label: "Research Agent", icon: Bot },
    { id: "approvals", label: "Approval Queue", icon: MailCheck, badge: approvalCount },
    { id: "campaigns", label: "Outreach Campaigns", icon: Send },
    { id: "suppressions", label: "Suppression List", icon: ShieldBan },
    { id: "audit", label: "Audit Logs", icon: ScrollText },
    { id: "settings", label: "Settings", icon: Settings },
  ];

  return (
    <aside className="w-64 bg-slate-950 border-r border-slate-800 flex flex-col shrink-0 min-h-screen">
      {/* Brand Logo */}
      <div className="h-16 flex items-center px-6 border-b border-slate-800 gap-3">
        <div className="w-9 h-9 rounded-lg bg-gradient-to-tr from-indigo-600 to-violet-500 flex items-center justify-center shadow-lg shadow-indigo-500/20">
          <Sparkles className="w-5 h-5 text-white" />
        </div>
        <div>
          <h1 className="font-bold text-sm tracking-wide text-white">INTELLIGENCE CRM</h1>
          <p className="text-[10px] text-slate-400 uppercase tracking-wider font-medium">Multi-Agent Outreach</p>
        </div>
      </div>

      {/* Nav List */}
      <nav className="flex-1 py-4 px-3 space-y-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onSelectTab(item.id)}
              className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 ${
                isActive
                  ? "bg-indigo-600/10 text-indigo-400 border border-indigo-500/20 shadow-sm"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-900/60"
              }`}
            >
              <div className="flex items-center gap-3">
                <Icon className={`w-4 h-4 ${isActive ? "text-indigo-400" : "text-slate-400"}`} />
                <span>{item.label}</span>
              </div>
              {item.badge !== undefined && item.badge > 0 && (
                <span className="px-2 py-0.5 text-xs font-semibold rounded-full bg-indigo-500 text-white">
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* Workspace Footer */}
      <div className="p-4 border-t border-slate-800">
        <div className="flex items-center gap-3 px-2 py-2 rounded-lg bg-slate-900/50">
          <div className="w-8 h-8 rounded-full bg-slate-800 flex items-center justify-center text-xs font-bold text-indigo-400">
            AE
          </div>
          <div className="overflow-hidden">
            <p className="text-xs font-semibold text-slate-200 truncate">Acme Enterprise</p>
            <p className="text-[11px] text-slate-400 truncate">Admin Workspace</p>
          </div>
        </div>
      </div>
    </aside>
  );
};
