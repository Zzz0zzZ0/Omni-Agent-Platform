"use client";
import Header from "@/components/Header";

export default function HistoryPage() {
  return (
    <>
      <Header
        currentRole=""
        roles={[]}
        onRoleChange={() => {}}
        onRefresh={() => {}}
        isConnected={false}
      />
      <div className="flex-1 overflow-y-auto p-8">
        <div className="max-w-7xl mx-auto animate-fade-in">
          <div className="mb-8">
            <h2 className="text-2xl font-bold">历史处理库</h2>
            <p className="text-[var(--text-secondary)] text-sm mt-1">
              归档的已处理工单与算法反馈记录
            </p>
          </div>

          <div className="glass-card rounded-2xl overflow-hidden border border-[var(--border)]">
            <table className="w-full text-left text-sm">
              <thead className="bg-white/5 text-[var(--text-secondary)]">
                <tr>
                  <th className="p-4 font-semibold uppercase text-[10px] tracking-wider">时间</th>
                  <th className="p-4 font-semibold uppercase text-[10px] tracking-wider">内容摘要</th>
                  <th className="p-4 font-semibold uppercase text-[10px] tracking-wider">处理人评分</th>
                  <th className="p-4 font-semibold uppercase text-[10px] tracking-wider">状态</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--border)]">
                <tr className="hover:bg-white/5 transition-colors">
                  <td className="p-4 text-[var(--text-secondary)]">2026-06-13 14:20</td>
                  <td className="p-4">充值未到帐 UID 10086...</td>
                  <td className="p-4">
                    <span className="text-emerald-400">+1.0 (Useful)</span>
                  </td>
                  <td className="p-4">
                    <span className="px-2 py-0.5 bg-emerald-500/10 text-emerald-400 rounded text-[10px] font-medium">
                      已归档
                    </span>
                  </td>
                </tr>
                <tr className="hover:bg-white/5 transition-colors opacity-50">
                  <td className="p-4 text-[var(--text-secondary)]">2026-06-13 12:10</td>
                  <td className="p-4">为什么不出限定角色专属武器？...</td>
                  <td className="p-4">
                    <span className="text-red-400">0.0 (Ignored)</span>
                  </td>
                  <td className="p-4">
                    <span className="px-2 py-0.5 bg-gray-500/10 text-gray-400 rounded text-[10px] font-medium">
                      已略过
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </>
  );
}
