"use client";

export default function StatCard({ label, value, change, changeType = "up", subtitle }) {
  const colors = {
    up: "text-emerald-400",
    down: "text-emerald-400",
    warning: "text-amber-400",
    neutral: "text-[var(--text-secondary)]",
  };

  return (
    <div className="glass-card p-6 rounded-2xl animate-fade-in hover:border-[var(--accent)]/20 transition-all duration-300">
      <p className="text-[var(--text-secondary)] text-[11px] uppercase tracking-wider mb-1.5 font-medium">
        {label}
      </p>
      <p className="text-3xl font-bold tracking-tight">{value}</p>
      {change && (
        <p className={`text-xs mt-2 flex items-center gap-1 ${colors[changeType]}`}>
          {change}
        </p>
      )}
      {subtitle && (
        <p className="text-xs mt-2 text-[var(--text-secondary)]">{subtitle}</p>
      )}
    </div>
  );
}
