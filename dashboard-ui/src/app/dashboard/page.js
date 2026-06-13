"use client";
import { useState, useEffect, useCallback } from "react";
import { TrendingUp, Bell } from "lucide-react";
import Header from "@/components/Header";
import StatCard from "@/components/StatCard";
import { fetchDashboardSummary, fetchDashboardConfig } from "@/lib/api";
import { useWebSocket } from "@/hooks/useWebSocket";

export default function DashboardPage() {
  const [summary, setSummary] = useState("");
  const [roles, setRoles] = useState([]);
  const [currentRole, setCurrentRole] = useState("");
  const [loading, setLoading] = useState(true);
  const { lastMessage, isConnected } = useWebSocket();

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [sumRes, configRes] = await Promise.all([
        fetchDashboardSummary(),
        fetchDashboardConfig(),
      ]);
      setSummary(sumRes.markdown || "暂无数据");
      if (configRes.roles) {
        setRoles(configRes.roles);
        if (!currentRole && configRes.roles.length > 0) {
          setCurrentRole(configRes.roles[0].id);
        }
      }
    } catch (err) {
      console.error("Failed to load dashboard:", err);
    } finally {
      setLoading(false);
    }
  }, [currentRole]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // WebSocket 实时更新
  useEffect(() => {
    if (lastMessage?.type === "ticket_processed") {
      loadData(); // 有新工单处理完成，刷新看板
    }
  }, [lastMessage, loadData]);

  return (
    <>
      <Header
        currentRole={currentRole}
        roles={roles}
        onRoleChange={setCurrentRole}
        onRefresh={loadData}
        isConnected={isConnected}
        alertCount={3}
        feedbackCount={12}
      />
      <div className="flex-1 overflow-y-auto p-8">
        <div className="max-w-7xl mx-auto space-y-8 animate-slide-up">
          <div className="flex items-center justify-between">
            <h2 className="text-2xl font-bold">全服舆情动态监控</h2>
            <span className="px-3 py-1 bg-emerald-500/10 text-emerald-400 text-xs rounded-full border border-emerald-500/20 font-medium">
              系统健康度: 98%
            </span>
          </div>

          <div className="grid grid-cols-3 gap-6">
            <StatCard label="今日处理总量" value="1,284" change="↑ 12.5% vs 昨日" changeType="up" />
            <StatCard label="平均响应时长" value="4.2m" change="↓ 0.8m vs 上周" changeType="down" />
            <StatCard label="冲突密集度" value="Medium" changeType="warning" subtitle="受卡池保底机制影响波动" />
          </div>

          <div className="glass-card p-8 rounded-2xl">
            <h3 className="font-bold mb-6 flex items-center gap-2 text-lg">
              <Bell size={18} className="text-[var(--accent)]" />
              实时冲突热力摘要
            </h3>
            {loading ? (
              <div className="text-center py-10 text-[var(--text-secondary)]">
                <div className="inline-block w-6 h-6 border-2 border-[var(--accent)]/30 border-t-[var(--accent)] rounded-full animate-spin" />
                <p className="mt-3 text-sm">正在生成 AI 摘要...</p>
              </div>
            ) : (
              <div className="prose prose-invert max-w-none text-[var(--text-secondary)] leading-relaxed text-sm whitespace-pre-wrap">
                {summary}
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
