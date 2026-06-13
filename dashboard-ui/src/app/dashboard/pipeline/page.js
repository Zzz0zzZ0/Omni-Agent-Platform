"use client";
import { useState, useEffect, useCallback } from "react";
import { TrendingUp } from "lucide-react";
import Header from "@/components/Header";
import TicketCard from "@/components/TicketCard";
import {
  fetchDashboardSummary,
  fetchDashboardTickets,
  fetchDashboardConfig,
  sendRecommendationFeedback,
} from "@/lib/api";
import { useWebSocket } from "@/hooks/useWebSocket";

export default function PipelinePage() {
  const [summary, setSummary] = useState("");
  const [tickets, setTickets] = useState([]);
  const [roles, setRoles] = useState([]);
  const [currentRole, setCurrentRole] = useState("");
  const [loading, setLoading] = useState(true);
  const { lastMessage, isConnected } = useWebSocket();

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [sumRes, tickRes, configRes] = await Promise.all([
        fetchDashboardSummary(),
        fetchDashboardTickets(),
        fetchDashboardConfig(),
      ]);
      setSummary(sumRes.markdown || "");
      setTickets(tickRes.tickets || []);
      if (configRes.roles) {
        setRoles(configRes.roles);
        if (!currentRole && configRes.roles.length > 0) {
          setCurrentRole(configRes.roles[0].id);
        }
      }
    } catch (err) {
      console.error("Failed to load pipeline:", err);
    } finally {
      setLoading(false);
    }
  }, [currentRole]);

  useEffect(() => { loadData(); }, [loadData]);

  useEffect(() => {
    if (lastMessage?.type === "ticket_processed") {
      loadData();
    }
  }, [lastMessage, loadData]);

  const handleAction = async (armIdx, contextVec, reward) => {
    try {
      await sendRecommendationFeedback(armIdx, contextVec, reward);
      loadData();
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <>
      <Header
        currentRole={currentRole}
        roles={roles}
        onRoleChange={setCurrentRole}
        onRefresh={loadData}
        isConnected={isConnected}
      />
      <div className="flex-1 overflow-y-auto p-8">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-12 gap-8 animate-fade-in">
            {/* Left: Summary */}
            <div className="col-span-4 space-y-6">
              <section className="glass-card rounded-2xl p-6">
                <div className="flex items-center justify-between mb-5">
                  <h2 className="text-base font-bold flex items-center gap-2">
                    <TrendingUp size={18} className="text-amber-400" />
                    今日社区核心矛盾
                  </h2>
                </div>
                <div className="text-sm text-[var(--text-secondary)] leading-relaxed whitespace-pre-wrap">
                  {summary || "暂无摘要"}
                </div>
              </section>

              <section className="glass-card rounded-2xl p-6 border-l-4 border-[var(--accent)]">
                <h3 className="font-bold mb-2 text-sm">LinUCB 推荐引擎</h3>
                <p className="text-xs text-[var(--text-secondary)] leading-relaxed">
                  当前对 <strong className="text-[var(--text-primary)]">
                    {roles.find((r) => r.id === currentRole)?.label || "..."}
                  </strong> 的分发权重已根据历史行为完成深度校准。
                </p>
              </section>
            </div>

            {/* Right: Tickets */}
            <div className="col-span-8">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold">待处理推荐流</h2>
                <span className="text-[10px] px-2 py-1 bg-white/5 rounded text-[var(--text-secondary)]">
                  基于 UCB 置信区间算法
                </span>
              </div>

              <div className="space-y-4">
                {loading ? (
                  <div className="text-center py-20 text-[var(--text-secondary)]">
                    <div className="inline-block w-6 h-6 border-2 border-[var(--accent)]/30 border-t-[var(--accent)] rounded-full animate-spin" />
                    <p className="mt-3 text-sm">加载反馈流水线中...</p>
                  </div>
                ) : tickets.length > 0 ? (
                  tickets.map((ticket) => (
                    <TicketCard
                      key={ticket.event_id}
                      ticket={ticket}
                      onAction={handleAction}
                    />
                  ))
                ) : (
                  <div className="text-center py-20 text-[var(--text-secondary)] glass-card rounded-2xl border-dashed border-white/5">
                    暂无待处理工单，系统正在持续感知中
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
