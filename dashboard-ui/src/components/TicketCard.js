"use client";
import { AlertCircle, CheckCircle, Clock, ThumbsUp, ThumbsDown } from "lucide-react";

const priorityColors = {
  P0: "bg-red-500/15 text-red-400 border-red-500/30",
  P1: "bg-amber-500/15 text-amber-400 border-amber-500/30",
  P2: "bg-blue-500/15 text-blue-400 border-blue-500/30",
  P3: "bg-gray-500/15 text-gray-400 border-gray-500/30",
};

export default function TicketCard({ ticket, onAction }) {
  const priority = ticket.priority || "P3";
  const colorClass = priorityColors[priority] || priorityColors.P3;

  return (
    <div className="glass-card rounded-2xl p-5 animate-fade-in hover:border-[var(--accent)]/15 transition-all duration-300 group">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-2">
            <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${colorClass}`}>
              {priority}
            </span>
            {ticket.is_crisis && (
              <span className="px-2 py-0.5 bg-red-500/20 text-red-400 border border-red-500/30 rounded text-[10px] font-bold flex items-center gap-1">
                <AlertCircle size={10} /> 高危
              </span>
            )}
            {ticket.recommended_operator && (
              <span className="px-2 py-0.5 bg-[var(--accent)]/10 text-[var(--accent)] rounded text-[10px] font-medium">
                → {ticket.recommended_operator}
              </span>
            )}
          </div>

          <p className="text-sm text-[var(--text-primary)] leading-relaxed line-clamp-2">
            {ticket.raw_text_content || ticket.structured_content || "No content"}
          </p>

          {ticket.tags && ticket.tags.length > 0 && (
            <div className="flex gap-1.5 mt-2 flex-wrap">
              {ticket.tags.map((tag, i) => (
                <span key={i} className="text-[10px] px-2 py-0.5 bg-white/5 rounded text-[var(--text-secondary)]">
                  {tag}
                </span>
              ))}
            </div>
          )}

          <div className="flex items-center gap-3 mt-3 text-[10px] text-[var(--text-secondary)]">
            <span className="flex items-center gap-1">
              <Clock size={10} />
              {ticket.timestamp ? new Date(ticket.timestamp).toLocaleString("zh-CN") : "Unknown"}
            </span>
            <span>ID: {(ticket.event_id || "").slice(0, 8)}...</span>
          </div>
        </div>

        {onAction && (
          <div className="flex flex-col gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
            <button
              onClick={() => onAction(ticket.arm_idx, ticket.context_vec, 1)}
              className="p-2 rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 transition-colors"
              title="标记处理"
            >
              <ThumbsUp size={14} />
            </button>
            <button
              onClick={() => onAction(ticket.arm_idx, ticket.context_vec, 0)}
              className="p-2 rounded-lg bg-red-500/10 hover:bg-red-500/20 text-red-400 transition-colors"
              title="忽略"
            >
              <ThumbsDown size={14} />
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
