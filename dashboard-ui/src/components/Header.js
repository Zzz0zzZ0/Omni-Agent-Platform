"use client";
import { AlertCircle, Bell, RefreshCw, Wifi, WifiOff } from "lucide-react";

export default function Header({ currentRole, roles, onRoleChange, onRefresh, isConnected, alertCount = 0, feedbackCount = 0 }) {
  return (
    <header className="h-16 border-b border-[var(--border)] flex items-center justify-between px-8 bg-[var(--bg-primary)]/50 backdrop-blur-md sticky top-0 z-10">
      <div className="flex items-center gap-6">
        <div className="text-sm flex items-center gap-2">
          <span className="text-[var(--text-secondary)]">当前视图:</span>
          <select
            value={currentRole}
            onChange={(e) => onRoleChange(e.target.value)}
            className="bg-transparent border-none font-bold text-[var(--accent)] focus:ring-0 cursor-pointer text-sm"
          >
            {roles.map((r) => (
              <option key={r.id} value={r.id} className="bg-[var(--bg-card)]">
                {r.label}
              </option>
            ))}
          </select>
        </div>

        <div className="h-6 w-px bg-[var(--border)]" />

        <div className="flex gap-3">
          {alertCount > 0 && (
            <div className="px-3 py-1 bg-red-500/10 border border-red-500/20 text-red-400 rounded-full text-[11px] font-semibold flex items-center gap-1">
              <AlertCircle size={12} />
              {alertCount} P0 告警
            </div>
          )}
          {feedbackCount > 0 && (
            <div className="px-3 py-1 bg-blue-500/10 border border-blue-500/20 text-blue-400 rounded-full text-[11px] font-semibold flex items-center gap-1">
              <Bell size={12} />
              {feedbackCount} 新反馈
            </div>
          )}
        </div>
      </div>

      <div className="flex items-center gap-4">
        <div className={`flex items-center gap-1.5 text-[11px] ${isConnected ? "text-emerald-400" : "text-red-400"}`}>
          {isConnected ? <Wifi size={12} /> : <WifiOff size={12} />}
          {isConnected ? "实时连接" : "离线"}
        </div>
        <button
          onClick={onRefresh}
          className="p-2 hover:bg-white/5 rounded-full text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors"
          title="刷新大盘"
        >
          <RefreshCw size={16} />
        </button>
      </div>
    </header>
  );
}
